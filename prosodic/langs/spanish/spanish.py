from ..langs import LanguageModel, get_sylls_ll, cache
from .spanish_annotator import make_annotation
import os
from ...imports import PATH_DICTS

stress2stroke = {0:'', 1:"'"}

orth2phon = {}

# Vowels
orth2phon['a'] = ['a']
orth2phon['e'] = ['e']
orth2phon['i'] = ['i']
orth2phon['o'] = ['o']
orth2phon['u'] = ['u']
orth2phon['á'] = ['a']
orth2phon['é'] = ['e']
orth2phon['í'] = ['i']
orth2phon['ó'] = ['o']
orth2phon['ú'] = ['u']
orth2phon['ü'] = ['w']  # used in güe/güi

# Diphthongs
orth2phon['ai'] = ['aj']
orth2phon['ei'] = ['ej']
orth2phon['oi'] = ['oj']
orth2phon['au'] = ['aw']
orth2phon['eu'] = ['ew']
orth2phon['ou'] = ['ow']
orth2phon['ia'] = ['ja']
orth2phon['ie'] = ['je']
orth2phon['io'] = ['jo']
orth2phon['ua'] = ['wa']
orth2phon['ue'] = ['we']
orth2phon['uo'] = ['wo']
orth2phon['ái'] = ['aj']
orth2phon['éi'] = ['ej']
orth2phon['ói'] = ['oj']
orth2phon['áu'] = ['aw']
orth2phon['éu'] = ['ew']
orth2phon['óu'] = ['ow']
orth2phon['ía'] = ['ja']
orth2phon['íe'] = ['je']
orth2phon['ío'] = ['jo']
orth2phon['úa'] = ['wa']
orth2phon['úe'] = ['we']
orth2phon['úo'] = ['wo']

# Consonants
orth2phon['b'] = ['b']
orth2phon['c'] = ['k']  # before a, o, u
orth2phon['ce'] = ['θ']  # in Spain; use ['s'] for Latin America
orth2phon['ci'] = ['θ']
orth2phon['ch'] = ['tʃ']
orth2phon['d'] = ['d']
orth2phon['f'] = ['f']
orth2phon['g'] = ['g']  # before a, o, u
orth2phon['ge'] = ['x']
orth2phon['gi'] = ['x']
orth2phon['gu'] = ['g']  # before e/i when ü is not used
orth2phon['gü'] = ['gw']
orth2phon['h'] = []  # silent
orth2phon['j'] = ['x']
orth2phon['k'] = ['k']
orth2phon['l'] = ['l']
orth2phon['ll'] = ['ʝ']  # or ['ʎ'] in some regions
orth2phon['m'] = ['m']
orth2phon['n'] = ['n']
orth2phon['ñ'] = ['ɲ']
orth2phon['p'] = ['p']
orth2phon['q'] = ['k']
orth2phon['qu'] = ['k']
orth2phon['r'] = ['ɾ']  # flap
orth2phon['rr'] = ['r']  # trill
orth2phon['s'] = ['s']
orth2phon['t'] = ['t']
orth2phon['v'] = ['b']  # same as b in most dialects
orth2phon['w'] = ['w']
orth2phon['x'] = ['ks']
orth2phon['y'] = ['ʝ']
orth2phon['z'] = ['θ']  # ['s'] in Latin America

ipa2x = dict([("".join(v), k) for (k, v) in orth2phon.items()])


class SpanishLanguage(LanguageModel):
    lang = 'es'
    name = 'spanish'
    lang_espeak = 'es-es'
    cache_fn = 'spanish_wordtypes'
    pronunciation_dictionary_filename = os.path.join(PATH_DICTS, 'es', 'spanish.tsv')

    @cache
    def get_sylls_ll_rule(self, token):
        token = token.strip()
        annotation = make_annotation(token)
        syllables = []
        wordbroken = False
        
        for ij in range(len(annotation.syllables)):
            try:
                sylldat = annotation.split_sylls[ij]
            except IndexError:
                sylldat = ["", "", ""]

            syllStr = ""
            onsetStr = sylldat[0].strip().replace("'", "").lower()
            nucleusStr = sylldat[1].strip().replace("'", "").lower()
            codaStr = sylldat[2].strip().replace("'", "").lower()

            # Process onset
            if onsetStr:
                if onsetStr in orth2phon:
                    syllStr += "".join(orth2phon[onsetStr])
                else:
                    for char in onsetStr:
                        if char in orth2phon:
                            syllStr += "".join(orth2phon[char])
                        else:
                            wordbroken = True
                            break

            # Process nucleus
            if nucleusStr:
                if nucleusStr in orth2phon:
                    syllStr += "".join(orth2phon[nucleusStr])
                else:
                    for char in nucleusStr:
                        if char in orth2phon:
                            syllStr += "".join(orth2phon[char])
                        else:
                            wordbroken = True
                            break

            # Process coda
            if codaStr:
                if codaStr in orth2phon:
                    syllStr += "".join(orth2phon[codaStr])
                else:
                    for char in codaStr:
                        if char in orth2phon:
                            syllStr += "".join(orth2phon[char])
                        else:
                            wordbroken = True
                            break

            if syllStr:
                syllables.append(syllStr)

        sylls_text = [syll for syll in annotation.syllables]
        sylls_ipa_ll = []
        sylls_text_ll = []
        
        for stress in annotation.stresses:
            sylls_ipa = [
                stress2stroke[stress[i]] + syllables[i] 
                for i in range(len(syllables))
            ]
            sylls_text_ll.append(sylls_text)
            sylls_ipa_ll.append(sylls_ipa)
            
        result = get_sylls_ll(sylls_ipa_ll, sylls_text_ll)
        if isinstance(result, tuple):
            return result
        else:
            return result, {'ipa_origin': 'rule', 'sylls_text_origin': 'rule'}

@cache
def Spanish(): return SpanishLanguage()
