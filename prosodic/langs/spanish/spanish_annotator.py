from ...imports import *
from .spanish_functions import *

class Annotation:
    def __init__(self, token):
        self.token = token.lower()  # Normalize to lowercase
        self.syllables = []
        self.stresses = []
        self.split_sylls = []
        self._analyze()

    def _analyze(self):
        # Split into syllables
        self.syllables = syllabify(self.token)
        
        # Get stress patterns
        self.stresses = get_stresses(self.token, self.syllables)
        
        # Split syllables into onset, nucleus, coda
        self.split_sylls = []
        for syll in self.syllables:
            onset, nucleus, coda = split_syllable(syll)
            self.split_sylls.append([onset, nucleus, coda])

def make_annotation(token):
    return Annotation(token)

def syllabify(token):
    """Split a word into syllables following Spanish phonetic rules."""
    token = token.lower().strip()
    
    # Handle empty or very short tokens
    if not token:
        return []
    if len(token) <= 1:
        return [token]
    
    # Define vowels and consonant groups
    vowels = {'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú', 'ü', 'y'}
    
    # Inseparable consonant clusters
    inseparable = {'pr', 'br', 'tr', 'dr', 'cr', 'gr', 'fr', 'kr',
                  'pl', 'bl', 'tl', 'dl', 'cl', 'gl', 'fl', 'kl',
                  'ch', 'll', 'rr', 'qu'}
    
    # Find all vowel positions
    positions = []
    for i, char in enumerate(token):
        if char in vowels:
            positions.append(i)
    
    # If no vowels found, return the whole token
    if not positions:
        return [token]
    
    # Divide into syllables according to Spanish rules
    syllables = []
    start = 0
    
    for i in range(len(positions) - 1):
        current_vowel_pos = positions[i]
        next_vowel_pos = positions[i + 1]
        
        # Distance between vowels
        distance = next_vowel_pos - current_vowel_pos
        
        if distance == 1:
            # Two consecutive vowels - check if they form a diphthong
            # Simple approach: if they're identical, they're separate syllables
            if token[current_vowel_pos] == token[next_vowel_pos]:
                syllables.append(token[start:current_vowel_pos + 1])
                start = current_vowel_pos + 1
            # For simplicity, assume other cases are diphthongs
        
        elif distance == 2:
            # One consonant between vowels - the consonant goes with the second vowel
            syllables.append(token[start:current_vowel_pos + 1])
            start = current_vowel_pos + 1
        
        elif distance == 3:
            # Two consonants between vowels
            cons_pair = token[current_vowel_pos + 1:next_vowel_pos]
            
            # Check for the specific case of 'st' which should be split
            if cons_pair == 'st':
                # Split after the first consonant (s-t)
                syllables.append(token[start:current_vowel_pos + 2])
                start = current_vowel_pos + 2
            # Check for other specific consonant pairs that should be split
            elif cons_pair in {'sp', 'sk', 'sc', 'ns', 'rs', 'nt', 'rt', 'lt', 'pt'}:
                # Split after the first consonant
                syllables.append(token[start:current_vowel_pos + 2])
                start = current_vowel_pos + 2
            # If it's an inseparable cluster, it goes with second vowel
            elif cons_pair in inseparable:
                syllables.append(token[start:current_vowel_pos + 1])
                start = current_vowel_pos + 1
            # Default: split between consonants
            else:
                syllables.append(token[start:current_vowel_pos + 2])
                start = current_vowel_pos + 2
        
        else:
            # Three or more consonants
            cons_group = token[current_vowel_pos + 1:next_vowel_pos]
            
            # Special case for 'st' in a larger group - handle "tristes" correctly
            if 'st' in cons_group:
                st_pos = cons_group.find('st')
                # Split before 's' if it's at the beginning, after 's' otherwise
                if st_pos == 0:
                    syllables.append(token[start:current_vowel_pos + 1])
                else:
                    syllables.append(token[start:current_vowel_pos + 1 + st_pos + 1])
                start = current_vowel_pos + 1 + st_pos + (0 if st_pos == 0 else 1)
            # Look for inseparable clusters at the beginning and end
            elif len(cons_group) >= 2 and cons_group[-2:] in inseparable:
                # Split before the inseparable cluster
                syllables.append(token[start:next_vowel_pos - 2])
                start = next_vowel_pos - 2
            elif len(cons_group) >= 2 and cons_group[:2] in inseparable:
                # Split after the first consonant if not part of inseparable cluster
                if len(cons_group) > 2:
                    syllables.append(token[start:current_vowel_pos + 2])
                    start = current_vowel_pos + 2
                else:
                    syllables.append(token[start:current_vowel_pos + 1])
                    start = current_vowel_pos + 1
            else:
                # Default: split in the middle of the consonant group
                mid = len(cons_group) // 2
                syllables.append(token[start:current_vowel_pos + 1 + mid])
                start = current_vowel_pos + 1 + mid
    
    # Add the last syllable
    syllables.append(token[start:])
    
    # Handle edge cases where syllabification doesn't add up to the original word
    if ''.join(syllables) != token:
        return [token]  # Return the whole word if something went wrong
    
    return syllables

def get_stresses(token, syllables=None):
    """Get stress patterns for a Spanish word"""
    token = token.lower()  # Normalize to lowercase
    
    if syllables is None:
        syllables = syllabify(token)
    
    # Handle empty token or no syllables
    if not token or not syllables:
        return [[]]
    
    num_syllables = len(syllables)
    
    # Default stress pattern: all unstressed
    stress = [0] * num_syllables
    
    # Monosyllabic words are always stressed
    if num_syllables == 1:
        stress[0] = 1
        return [stress]
    
    # Check for written accent marks
    for i, syll in enumerate(syllables):
        if any(c in syll for c in ['á', 'é', 'í', 'ó', 'ú']):
            stress[i] = 1
            return [stress]
    
    # Apply default stress rules:
    # - Words ending in vowel, n, or s: stress on penultimate syllable
    # - All other words: stress on final syllable
    if token[-1] in {'a', 'e', 'i', 'o', 'u', 'n', 's'}:
        if num_syllables >= 2:
            stress[-2] = 1  # Penultimate
        else:
            stress[0] = 1   # Only syllable
    else:
        stress[-1] = 1      # Final syllable
    
    return [stress]

def split_syllable(syllable):
    """Split a syllable into onset, nucleus, and coda"""
    syllable = syllable.lower()  # Normalize to lowercase
    
    # Handle empty syllable
    if not syllable:
        return "", "", ""
    
    vowels = {'a', 'e', 'i', 'o', 'u', 'á', 'é', 'í', 'ó', 'ú', 'ü'}
    
    # Find the first vowel (start of nucleus)
    nucleus_start = 0
    while nucleus_start < len(syllable) and syllable[nucleus_start] not in vowels:
        nucleus_start += 1
    
    # If no vowels found, treat the whole syllable as onset
    if nucleus_start >= len(syllable):
        return syllable, "", ""
    
    # Find the end of the nucleus (all consecutive vowels)
    nucleus_end = nucleus_start
    while nucleus_end < len(syllable) and syllable[nucleus_end] in vowels:
        nucleus_end += 1
    
    onset = syllable[:nucleus_start]
    nucleus = syllable[nucleus_start:nucleus_end]
    coda = syllable[nucleus_end:]
    
    return onset, nucleus, coda 