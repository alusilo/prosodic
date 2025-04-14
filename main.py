import prosodic

sentence = "Der Himmel ist blau. Die Erde ist grün. Die Wiese ist grün."
language = "de"

sonnet = prosodic.Text(sentence, lang=language)

# print(sonnet.df)
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
