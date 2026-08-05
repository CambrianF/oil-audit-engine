# Case Study: Finding a Silent Overcharge Bug Through Stress Testing

## The setup

I built a rule-checking engine to audit oilfield rental invoices — for example, catching when United Rentals bills a daily rate for longer than the contract's threshold, when it should have converted to a cheaper weekly rate. My first version matched a very specific sentence structure:

`"Rental Days Billed: 50 @ Daily Rate $185.00/day"`

I tested it against a handful of invoices I generated myself, and it worked — every rate-roll violation I built into the test data got caught correctly.

## Why that wasn't good enough

I decided to deliberately try to break my own system before trusting it. Instead of testing with invoices that matched the pattern I'd written the code around, I wrote a test invoice describing the exact same violation in plain, different language:

`"This unit has been on rent for 45 days at a rate of $175.00 per day."`

Same fact. Same violation — 45 days exceeds the 28-day threshold. Different sentence structure.

The result: **the invoice passed clean.** No flag, no warning. My rule engine looked for one specific phrase pattern and found nothing, so it silently moved on — meaning a real overcharge would have gone completely undetected if this had been an actual vendor invoice.

This was the single most important thing I found across two days of testing, because it wasn't a crash or an obviously wrong result. It was quiet. An AP clerk would have seen "Passed" and paid the invoice without a second look. A tool that fails loudly is annoying; a tool that fails silently is dangerous, especially in a domain where the entire point is catching money that's slipping out the door.

## The fix

I replaced the single rigid regex pattern with proximity-based extraction: instead of requiring one exact sentence template, the code now searches for a day-count near duration-related language ("days," "on rent," "billed for") and a dollar amount near rate-related language ("rate," "per day," "/day") anywhere in the document, independent of the surrounding sentence structure. This let the same underlying fact get extracted correctly regardless of how it was phrased.

I re-ran the exact test that had failed. It now correctly flagged the 45-day rental as a rate-roll violation, with the right dollar figures.

## Why I'm writing this down

I could have stopped after the first version worked on my initial test invoices. It's tempting to treat "it passed my tests" as proof something is done. But my own tests were written with the same assumptions as my code — of course they matched. The value came from deliberately trying to find a case my own logic hadn't anticipated, rather than only confirming what I already expected to work.

I found a second, related bug the same way a few hours later: my code was silently dropping the minus sign on negative dollar amounts (credits), which meant a large legitimate credit could theoretically have been misread as a charge that exceeds a cap. I traced the actual mechanism instead of accepting that a test "passed" — the first version of my negative-number test happened to pass by coincidence (the credit amount was small enough to stay under the cap either way), not because the bug didn't exist. Only by specifically constructing a test that would expose the bug if it existed did I find the fix that mattered.

The lesson I'm taking into the rest of this project: a passing test only tells you your code handles what you thought to test. Deliberately trying to break your own assumptions — not just confirming them — is where the real bugs get found.

## A third bug: assuming state never changes

After building the ghost-rental detection feature, I tested it two ways: a unit that was billed past its official return date (correctly flagged), and a unit billed exactly up to its return date (correctly passed, no false positive on the boundary). Both worked. I was ready to call the feature done.

Before moving on, I asked myself a question specific to this feature: what happens when the same piece of equipment gets called off, and then legitimately rented again later? This is completely normal in oilfield operations — a generator gets returned after one job and rented again for the next.

I tested it, and found the bug immediately: my ledger only tracked "was this unit ever called off," with no concept of time passing afterward. A brand-new, completely legitimate rental of a previously-returned unit was getting flagged as a ghost rental — forever, on every future invoice for that unit — because the system had no way to distinguish "still on the old rental" from "on a new one."

## Why this one mattered more than it looked

The first two bugs I found (phrasing brittleness, sign handling) were "this specific case is wrong" bugs — narrow, contained, findable by testing edge cases. This one was different: it wasn't a bug in one check, it was a bug in an assumption baked into the entire feature's design — that once a unit is marked "called off," any future invoice for that serial number is suspect. That assumption is wrong the moment you account for equipment being reused, which is the normal case, not the edge case, in this industry.

If I hadn't caught this, the ghost-rental detector — the single feature I built specifically because my own research identified it as the highest-value capability for this product — would have started producing false positives on ordinary business as soon as any vendor reused equipment. A tool that cries wolf on normal operations gets ignored, and an ignored audit tool is worse than no audit tool, because it creates a false sense of coverage.

## The fix

I added a check on the invoice'"'"'s contract start date: if the new rental'"'"'s start date is after the recorded call-off date, it'"'"'s treated as a legitimate new rental, not a continuation of the old one — regardless of the fact that the serial number matches a "called off" ledger entry. I tested it against the exact re-rental scenario, using the same unit that was already flagged as a real ghost rental elsewhere in my test data, to make sure the fix didn'"'"'t accidentally break the case it was supposed to still catch. Both held: the genuine ghost rental still flagged, and the legitimate re-rental correctly passed clean.

The broader lesson: it'"'"'s not enough to test whether a feature handles the scenario you built it for. You also have to ask what happens as time passes and the real-world state your system is modeling keeps changing — because a system that only makes sense at the moment you built it is a system that will quietly start lying to you later.

## A fourth bug: the error that hid itself

While testing the ghost-rental feature against out-of-order data (what happens if a call-off confirmation arrives late, after a more recent one is already on file), I built a safeguard: reject an incoming call-off date if it'"'"'s older than what'"'"'s already recorded for that unit, rather than silently overwriting good data with stale data.

I tested it. It didn'"'"'t work. I fixed the ledger'"'"'s stored data by hand and tested again. It still didn'"'"'t work. I checked the code — the rejection logic was correct, verified by reading the actual file contents. I checked for a stale Python cache — cleared it, still didn'"'"'t work. I checked for duplicate files elsewhere on disk — none existed. Every individual piece I could inspect was correct, and yet the behavior was consistently wrong.

## Finding it

The actual bug wasn'"'"'t in the rejection logic at all. It was in the function that loads the ledger file from disk:

```python
def load_ledger():
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}
```

Every time I'"'"'d rewritten the ledger file from the terminal, the tool I used had embedded an invisible marker at the start of the file (a byte-order mark, or BOM) — the same category of issue I'"'"'d already hit once before with a CSV file, but I hadn'"'"'t connected the two. That invisible character made `json.load()` fail. And the `except Exception: return {}` line — written defensively, to keep the program from crashing if the ledger file didn'"'"'t exist yet — was silently catching that failure and returning an empty dictionary instead.

An empty ledger doesn'"'"'t look broken. It looks like a ledger with no entries yet. So every "existing entry" check I ran saw nothing there, treated every incoming record as brand new, and happily overwrote whatever had been there before — including, each time, quietly erasing prior entries that weren'"'"'t part of that specific run. I spent several rounds fixing the data and re-testing, and every fix looked like it failed, because the file was never actually being read at all.

## Why this was harder to find than the other three

The first three bugs I found all had a common shape: the code ran, produced an answer, and the answer was wrong. That'"'"'s findable by testing — you compare what you expected to what you got, and the mismatch points you at the problem.

This one was different. The code wasn'"'"'t producing a wrong answer. It was failing completely, silently, and then behaving as if nothing had gone wrong. There was no error message, no traceback, no signal at all that something had broken — because the broad exception handler was specifically written to prevent exactly that kind of visible failure. The safety mechanism I'"'"'d added to keep the program from crashing was the same mechanism hiding the actual defect.

## The lesson

A broad `except Exception:` that silently swallows an error and returns a harmless-looking default is a reasonable thing to reach for — nobody wants their program to crash on a missing file. But it comes with a cost: it can hide a real bug so completely that the bug becomes invisible to every kind of testing except staring directly at the one function where the exception is being caught. I only found this by refusing to accept "the code looks right" as an answer, and manually verifying, one command at a time, exactly what was happening at each step — not just what the code said it should do, but what the file on disk actually contained at each point in the process.

Going forward, I want any exception handler I write to at least log or print what it caught, not just silently substitute a default — a failure that announces itself is a bug you find in minutes; a failure that hides itself is a bug you find in hours, if you find it at all.

## A sixth bug: an assumption baked into every check at once

Every check I had built for United Rentals - rate-roll, the Environmental Service Charge cap, the unauthorized RPP fee check - relied on functions that searched the document for the first matching line and stopped there. That worked perfectly on every test invoice I had built, because every one of them represented a single piece of equipment.

After fixing the earlier gap around multi-line-item invoices for a different vendor, I asked myself a harder version of the same question: what happens on a United Rentals invoice that bills for more than one unit at once? A single delivery, one invoice, two pieces of equipment - completely normal in real oilfield operations, where an operator might rent a light tower and a generator for the same lease on the same day.

I built the test: two units on one invoice, the first unit'"'"'s Environmental Service Charge well under the cap, the second unit'"'"'s charge well over it. I ran it. The invoice came back completely clean.

## Why this one was worse than it looked

This wasn'"'"'t one broken check. It was one broken assumption, copy-pasted into three separate checks. Rate-roll, the fee cap, and the unauthorized-fee detector all used the same "find the first match and stop" pattern, because I had written them at different times without noticing they shared the same underlying limitation. A single design mistake, made once early on, had silently propagated into every rule I built afterward for that vendor - and it would keep propagating into any new rule I added later, unless I fixed the pattern itself rather than patching one check at a time.

The real overcharge in my test - a genuine $180 fee against a $99 cap - was sitting in plain text in the invoice, extracted correctly by the underlying regex, and simply never reached, because the code stopped looking after the first hit.

## The fix

I changed every relevant extraction function from "return the first match" to "return every match," and changed the checks that used them to loop over all of the results instead of just the one. The fix used a pattern that already existed correctly elsewhere in my own codebase - a different function, built earlier for a different vendor, had never made this mistake in the first place. I just hadn'"'"'t noticed the inconsistency until I went looking for it on purpose.

## The lesson

A bug that lives in one function is contained. A bug that lives in an assumption gets copied every time that assumption gets reused - and the more useful and well-tested a piece of code looks, the more likely it is to get reused without anyone questioning the premise it was built on. The fix here wasn'"'"'t really about regex. It was about noticing that "check the first thing found" had quietly become an unstated rule I was applying everywhere, and that the only way to find out whether that rule was safe was to build the one document specifically designed to break it.
