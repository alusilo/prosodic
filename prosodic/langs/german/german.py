from ..langs import LanguageModel, cache

stress2stroke = {0:'', 1:"'"}

orth2phon = {}

# Vowels (short)
orth2phon['a'] = ['a']
orth2phon['e'] = ['ɛ']
orth2phon['i'] = ['ɪ']
orth2phon['o'] = ['ɔ']
orth2phon['u'] = ['ʊ']
orth2phon['ä'] = ['ɛ']
orth2phon['ö'] = ['œ']
orth2phon['ü'] = ['ʏ']

# Vowels (long)
orth2phon['aa'] = ['aː']
orth2phon['ah'] = ['aː']
orth2phon['ee'] = ['eː']
orth2phon['eh'] = ['eː']
orth2phon['ie'] = ['iː']
orth2phon['ih'] = ['iː']
orth2phon['oo'] = ['oː']
orth2phon['oh'] = ['oː']
orth2phon['uu'] = ['uː']
orth2phon['uh'] = ['uː']
orth2phon['öh'] = ['øː']
orth2phon['üh'] = ['yː']
orth2phon['ää'] = ['ɛː']

# Diphthongs
orth2phon['au'] = ['aʊ̯']
orth2phon['ei'] = ['aɪ̯']
orth2phon['ai'] = ['aɪ̯']
orth2phon['eu'] = ['ɔʏ̯']
orth2phon['äu'] = ['ɔʏ̯']

# Consonants
orth2phon['b'] = ['b']
orth2phon['c'] = ['k']  # typically before 'a', 'o', 'u'
orth2phon['ch'] = ['ç']  # or ['x'] depending on context
orth2phon['d'] = ['d']
orth2phon['f'] = ['f']
orth2phon['g'] = ['g']
orth2phon['h'] = ['h']
orth2phon['j'] = ['j']
orth2phon['k'] = ['k']
orth2phon['l'] = ['l']
orth2phon['m'] = ['m']
orth2phon['n'] = ['n']
orth2phon['ng'] = ['ŋ']
orth2phon['p'] = ['p']
orth2phon['qu'] = ['kv']
orth2phon['r'] = ['ʁ']
orth2phon['s'] = ['z']  # usually /z/ between vowels, can be /s/
orth2phon['ß'] = ['s']
orth2phon['sch'] = ['ʃ']
orth2phon['sp'] = ['ʃp']
orth2phon['st'] = ['ʃt']
orth2phon['t'] = ['t']
orth2phon['v'] = ['f']
orth2phon['w'] = ['v']
orth2phon['x'] = ['ks']
orth2phon['y'] = ['ʏ']  # as vowel, sometimes pronounced /y/
orth2phon['z'] = ['ts']

ipa2x=dict([("".join(v), k) for (k, v) in orth2phon.items()])


class GermanLanguage(LanguageModel):
    lang = 'de'
    name = 'german'
    lang_espeak = 'de-de'

@cache
def German(): return GermanLanguage()
