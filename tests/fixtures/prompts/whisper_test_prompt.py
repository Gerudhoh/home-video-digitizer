def whisper_test_prompt():
    return """
    Grade a Whisper transcript of a home video against a hand-written "golden"
    transcript of the same audio (informal camcorder footage: overlapping
    speakers, background noise, pre-verbal babbling, family nicknames).

    Judge by meaning, not exact string match.

    IGNORE: punctuation/case/whitespace; missing filler words if meaning
    holds; different segment/line splits as long as content appears somewhere;
    approximate phonetic renderings of babbling/vocalizations.

    PENALIZE: misheard/substituted proper names; dropped lines with
    substantive content; changes to who said what or what happened.

    Score 0-1:
    - 1.0: same names/speakers/events, only cosmetic differences
    - 0.7-0.9: names/content correct, minor omissions or rewording
    - 0.4-0.6: names or key events wrong/missing but gist recoverable
    - 0.0-0.3: misrepresents who was there or what happened

    Respond with ONLY this JSON, no surrounding text or code fences:
    {"score": <float 0-1>, "comments": [<string per notable difference>]}

    Each comment should name the specific discrepancy, not summarize. Empty
    list if none.

    The Transcripts are as follows:
    """
