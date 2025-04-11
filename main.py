import prosodic

sentence = "Die Leute sind zufrieden und die Leute sind glücklich."
language = "de"

sonnet = prosodic.Text(sentence, lang=language)
for parse in sonnet.parses:
    print(parse.__dict__)
print(sonnet.df)
for stanza in sonnet.stanzas:
    for line in stanza.lines:
        for word_token in line:
            print(word_token)
            for word_type in word_token:
                for word_form in word_type:
                    for syllable in word_form:
                        print(syllable)
                        for phoneme in syllable:
                            print(phoneme)
