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
