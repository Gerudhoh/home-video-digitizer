def whisper_test_prompt():
    return """
    You are grading a Whisper transcript of a home video against a hand-written
    "golden" transcript of the same audio. The audio is informal home-camcorder
    footage: multiple overlapping speakers, background noise, young children
    (including pre-verbal babbling), and family nicknames or proper names.

    Judge similarity by meaning, not by exact string match. Specifically:

    IGNORE (do not penalize):
    - Punctuation, capitalization, and whitespace differences
    - Missing filler words/interjections ("um", "uh", "whoops") if the
      surrounding meaning is intact
    - Differences in how the text is split into segments/lines (Whisper may
      merge several golden lines into one segment, or vice versa) as long as
      the same content appears somewhere in the transcript
    - Approximate phonetic renderings of toddler babbling or non-lexical
      vocalizations, as long as both transcripts indicate speech/vocalization
      occurred at that point

    PENALIZE:
    - Misheard or substituted proper names (e.g. "Kath" transcribed as "Cat")
    - Dropped lines/sentences that contain substantive spoken content
    - Changes that alter who said something or what happened (factual/intent
      drift), not just word choice

    Score the overall similarity as a single float between 0 and 1, using
    these anchors:
    - 1.0: same names, same speakers, same events/content; only cosmetic
      differences (punctuation, filler words, segmentation)
    - 0.7-0.9: content and names correct, but some minor omissions or
      rewording of non-critical dialogue
    - 0.4-0.6: names or key events are wrong or missing, but the general
      gist/topic is still recoverable
    - 0.0-0.3: the transcript misrepresents who was there or what happened,
      or is largely unrelated to the golden transcript

    Respond with ONLY a JSON object matching this schema, and nothing else -
    no surrounding text, no markdown code fences:

    {
      "score": <float, 0 to 1>,
      "comments": [<string, one short comment per notable difference>]
    }

    Each entry in "comments" should name the specific discrepancy (e.g.
    "misheard Kath as Cat", "dropped line: 'Whoops'"), not a general summary.
    If there are no notable differences, return an empty list for "comments".
    """