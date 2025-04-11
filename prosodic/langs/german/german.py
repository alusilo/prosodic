from ...imports import *
from ..langs import LanguageModel, get_sylls_ll
from .german_annotator import make_annotation
import re
from functools import cache
from enum import Enum, auto
from typing import List, Tuple, Dict, Optional, Union, Set

# Phonetic mappings for German orthography to IPA
GRAPHEME_TO_PHONEME = {
    # Vowels
    'a': 'a', 'e': 'ə', 'i': 'ɪ', 'o': 'ɔ', 'u': 'ʊ',
    'ä': 'ɛ', 'ö': 'œ', 'ü': 'y',
    # Long vowels often doubled or followed by 'h'
    'aa': 'aː', 'ee': 'eː', 'oo': 'oː', 'uu': 'uː',
    'ah': 'aː', 'eh': 'eː', 'ih': 'iː', 'oh': 'oː', 'uh': 'uː',
    'äh': 'ɛː', 'öh': 'øː', 'üh': 'yː',
    # Consonants
    'b': 'b', 'c': 'k', 'd': 'd', 'f': 'f', 'g': 'g', 'h': 'h',
    'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'p': 'p',
    'q': 'k', 'r': 'ʁ', 's': 's', 't': 't', 'v': 'f', 'w': 'v',
    'x': 'ks', 'y': 'y', 'z': 'ts',
    # Common digraphs
    'ch': 'x', 'ck': 'k', 'ph': 'f', 'qu': 'kv', 'sch': 'ʃ', 
    'sp': 'ʃp', 'st': 'ʃt', 'th': 't', 'tz': 'ts',
    'ng': 'ŋ', 'nk': 'ŋk',
}

# Common German diphthongs
DIPHTHONGS = {
    'ei': 'aɪ̯', 'ai': 'aɪ̯', 'ey': 'aɪ̯', 'ay': 'aɪ̯',
    'au': 'aʊ̯',
    'eu': 'ɔɪ̯', 'äu': 'ɔɪ̯',
    'ie': 'iː',  # Not technically a diphthong but a common digraph
}

stress2stroke = {0:'', 1:"'", 2:"`"}

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
orth2phon['äh'] = ['ɛː']
orth2phon['ää'] = ['ɛː']
orth2phon['öh'] = ['øː']
orth2phon['üh'] = ['yː']

# Diphthongs
orth2phon['au'] = ['aʊ̯']
orth2phon['ei'] = ['aɪ̯']
orth2phon['ai'] = ['aɪ̯']
orth2phon['eu'] = ['ɔʏ̯']
orth2phon['äu'] = ['ɔʏ̯']

# Consonants
orth2phon['b'] = ['b']
orth2phon['b#'] = ['p']  # Terminal devoicing
orth2phon['c'] = ['k']   # normally before a, o, u
orth2phon['c+'] = ['ts'] # before i, e (Latin/Romance loanwords)
orth2phon['ch'] = ['ç']  # after front vowels (i, e, ä, ö, ü)
orth2phon['ach'] = ['x'] # after back vowels (a, o, u)
orth2phon['chs'] = ['ks']
orth2phon['ck'] = ['k']
orth2phon['d'] = ['d']
orth2phon['d#'] = ['t']  # Terminal devoicing
orth2phon['dt'] = ['t']
orth2phon['f'] = ['f']
orth2phon['g'] = ['g']
orth2phon['g#'] = ['k']  # Terminal devoicing
orth2phon['h'] = ['h']
orth2phon['j'] = ['j']
orth2phon['k'] = ['k']
orth2phon['l'] = ['l']
orth2phon['m'] = ['m']
orth2phon['n'] = ['n']
orth2phon['ng'] = ['ŋ']
orth2phon['nk'] = ['ŋk']
orth2phon['p'] = ['p']
orth2phon['pf'] = ['pf']
orth2phon['ph'] = ['f']
orth2phon['qu'] = ['kv']
orth2phon['r'] = ['ʁ']
orth2phon['s'] = ['z']   # Before vowels at the start or within words
orth2phon['s#'] = ['s']  # At end of syllables or before consonants
orth2phon['ss'] = ['s']
orth2phon['ß'] = ['s']
orth2phon['sch'] = ['ʃ']
orth2phon['sp'] = ['ʃp'] # At beginning of words or syllables
orth2phon['st'] = ['ʃt'] # At beginning of words or syllables
orth2phon['t'] = ['t']
orth2phon['th'] = ['t']
orth2phon['ti+'] = ['tsi'] # in -tion, -tial (loanwords)
orth2phon['tz'] = ['ts']
orth2phon['v'] = ['f']   # Usually 'f' in native German words
orth2phon['v+'] = ['v']  # In loanwords (Vase, Virus)
orth2phon['w'] = ['v']
orth2phon['x'] = ['ks']
orth2phon['y'] = ['ʏ']   # As vowel
orth2phon['z'] = ['ts']

ipa2x = dict([("".join(v), k) for (k, v) in orth2phon.items()])

class GermanLanguage(LanguageModel):
    pronunciation_dictionary_filename = os.path.join(PATH_DICTS, 'de', 'german.tsv')
    lang = 'de'
    cache_fn = 'german_wordtypes'

    @cache
    def get_sylls_ll_rule(self, token):
        token = token.strip().lower()
        Annotation = make_annotation(token)
        
        # Check if any syllables are duplicated
        syllables_unique = []
        seen = set()
        for syll in Annotation.syllables:
            if syll not in seen:
                syllables_unique.append(syll)
                seen.add(syll)
        
        # If we detected duplicated syllables, recreate the annotation with deduplicated syllables
        if len(syllables_unique) < len(Annotation.syllables):
            # Create a new token by joining unique syllables
            token_deduplicated = ''.join(syllables_unique)
            Annotation = make_annotation(token_deduplicated)
        
        # Process syllables to IPA
        syllables = []
        for ij in range(len(Annotation.syllables)):
            try:
                sylldat = Annotation.split_sylls[ij]
            except IndexError:
                sylldat = ["", "", ""]

            # Extract the parts of the syllable
            onsetStr = sylldat[0].strip().lower()
            nucleusStr = sylldat[1].strip().lower()
            codaStr = sylldat[2].strip().lower()
            
            # Create the IPA transcription for this syllable
            syllable_ipa = self.transcribe_syllable_parts(onsetStr, nucleusStr, codaStr, 
                                                         is_final=(ij == len(Annotation.syllables) - 1))
            syllables.append(syllable_ipa)

        # Build the syllable lists
        sylls_text = Annotation.syllables  # Use syllables directly, don't copy
        sylls_ipa_ll = []
        sylls_text_ll = []
        
        # Apply stress patterns
        for stress in Annotation.stresses:
            # Validate that stress is a list or string
            if isinstance(stress, list):
                stress_vals = stress
            else:
                # Convert string to list of integers
                stress_vals = [int(c) for c in stress if c.isdigit()]
                
            # Create stressed syllables 
            sylls_ipa = []
            for i in range(min(len(syllables), len(stress_vals))):
                # Ensure stress value is valid (0, 1, or a 2 we can handle)
                stress_val = stress_vals[i]
                if stress_val not in stress2stroke:
                    # Default to unstressed if not recognized
                    stress_val = 0
                    
                sylls_ipa.append(stress2stroke[stress_val] + syllables[i])
            
            # Pad with unstressed syllables if needed
            if len(syllables) > len(stress_vals):
                for i in range(len(stress_vals), len(syllables)):
                    sylls_ipa.append(syllables[i])  # Unstressed
            
            # Store the stress variant
            sylls_text_ll.append(sylls_text)
            sylls_ipa_ll.append(sylls_ipa)
        
        # Handle case where there are no stresses
        if not sylls_ipa_ll:
            sylls_ipa_ll.append(syllables)
            sylls_text_ll.append(sylls_text)
            
        # Return the results
        result = get_sylls_ll(sylls_ipa_ll, sylls_text_ll)
        if isinstance(result, tuple):
            return result
        else:
            return result, {'ipa_origin': 'rule', 'sylls_text_origin': 'rule'}
    
    def transcribe_syllable_parts(self, onset, nucleus, coda, is_final=False):
        """Transcribe syllable parts to IPA following German phonetic rules"""
        ipa = ""
        
        # Process onset (consonants before the vowel)
        if onset:
            if onset in orth2phon:
                # Handle special multi-character onsets like 'sch', 'ch'
                ipa += "".join(orth2phon[onset])
            else:
                # Process character by character for normal onsets
                i = 0
                while i < len(onset):
                    # Check for digraphs and trigraphs first
                    if i < len(onset) - 2 and onset[i:i+3] in orth2phon:
                        ipa += "".join(orth2phon[onset[i:i+3]])
                        i += 3
                    elif i < len(onset) - 1 and onset[i:i+2] in orth2phon:
                        ipa += "".join(orth2phon[onset[i:i+2]])
                        i += 2
                    else:
                        # Single character
                        char_phon = orth2phon.get(onset[i], [''])
                        ipa += "".join(char_phon)
                        i += 1
        
        # Process nucleus (vowel or diphthong)
        if nucleus:
            if nucleus in orth2phon:
                # Handle special cases like diphthongs directly
                ipa += "".join(orth2phon[nucleus])
            elif len(nucleus) == 2:
                # Check for special vowel combinations
                if nucleus[0] == nucleus[1]:  # Double vowel (e.g., 'aa', 'ee')
                    long_key = nucleus[0]*2
                    if long_key in orth2phon:
                        ipa += "".join(orth2phon[long_key])
                    else:
                        # If no specific mapping, use the individual vowels
                        for char in nucleus:
                            if char in orth2phon:
                                ipa += "".join(orth2phon[char])
                elif nucleus in {'ie', 'ei', 'ai', 'eu', 'äu', 'au'}:  # Known diphthongs
                    ipa += "".join(orth2phon.get(nucleus, ['']))
                elif nucleus[1] == 'h':  # Vowel + h (lengthening)
                    long_key = nucleus[0] + 'h'
                    if long_key in orth2phon:
                        ipa += "".join(orth2phon[long_key])
                    else:
                        # If no specific mapping, handle as separate characters
                        for char in nucleus:
                            if char in orth2phon:
                                ipa += "".join(orth2phon[char])
                else:
                    # Process as individual characters
                    for char in nucleus:
                        if char in orth2phon:
                            ipa += "".join(orth2phon[char])
            else:
                # Single vowel or complex nucleus - process character by character
                for char in nucleus:
                    if char in orth2phon:
                        ipa += "".join(orth2phon[char])
        
        # Process coda (consonants after the vowel)
        if coda:
            # Handle final devoicing for the last syllable
            if is_final:
                processed_coda = self.apply_final_devoicing(coda)
            else:
                processed_coda = coda
                
            i = 0
            while i < len(processed_coda):
                # Check for special consonant clusters
                if i < len(processed_coda) - 2 and processed_coda[i:i+3] in orth2phon:
                    ipa += "".join(orth2phon[processed_coda[i:i+3]])
                    i += 3
                elif i < len(processed_coda) - 1 and processed_coda[i:i+2] in orth2phon:
                    ipa += "".join(orth2phon[processed_coda[i:i+2]])
                    i += 2
                else:
                    char = processed_coda[i]
                    # Use terminal devoicing for word-final position
                    if is_final and i == len(processed_coda) - 1:
                        if char == 'b':
                            ipa += "".join(orth2phon.get('b#', ['p']))
                        elif char == 'd':
                            ipa += "".join(orth2phon.get('d#', ['t']))
                        elif char == 'g':
                            ipa += "".join(orth2phon.get('g#', ['k']))
                        elif char == 'v' or char == 'w':
                            ipa += "".join(orth2phon.get('f', ['f']))
                        elif char == 'z':
                            ipa += "".join(orth2phon.get('s#', ['s']))
                        else:
                            ipa += "".join(orth2phon.get(char, ['']))
                    else:
                        ipa += "".join(orth2phon.get(char, ['']))
                    i += 1
        
        return ipa
    
    def apply_final_devoicing(self, coda):
        """Apply German terminal devoicing rules"""
        if not coda:
            return coda
            
        # Simple terminal devoicing rules
        result = coda
        if result.endswith('b'):
            result = result[:-1] + 'p'
        elif result.endswith('d'):
            result = result[:-1] + 't'
        elif result.endswith('g'):
            result = result[:-1] + 'k'
        elif result.endswith('s') and len(result) > 1:
            # If 's' is preceded by a voiced consonant, devoice that too
            if result[-2] in 'bdgvz':
                if result[-2] == 'b':
                    result = result[:-2] + 'ps'
                elif result[-2] == 'd':
                    result = result[:-2] + 'ts'
                elif result[-2] == 'g':
                    result = result[:-2] + 'ks'
                elif result[-2] == 'v':
                    result = result[:-2] + 'fs'
                elif result[-2] == 'z':
                    result = result[:-2] + 'ss'
                    
        return result

@cache
def German(): return GermanLanguage()
