from .imports import *
from .constraints import *


@total_ordering
class Parse(Entity):
    prefix = "parse"

    def __init__(
        self,
        wordforms_or_str,
        scansion: str = "",
        meter: "Meter" = None,
        parent=None,
        positions=None,
        is_bounded=False,
        bounded_by=None,
        rank=None,
        line_num=None,
        stanza_num=None,
        line_txt="",
    ):
        from .meter import Meter

        if not positions:
            positions = []
        self.positions = positions

        # meter
        if meter is None:
            meter = Meter()
        self.meter_obj = self.meter = meter

        # wordforms
        assert wordforms_or_str
        if hasattr(wordforms_or_str, "is_parseable") and wordforms_or_str.is_parseable:
            parent = wordforms_or_str
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str) == str:
            parent = Line(wordforms_or_str)
            self.wordforms = meter.get_wordform_matrix(parent)[0]
        elif type(wordforms_or_str) == list:
            from .lists import WordFormList
            self.wordforms = WordFormList(wordforms_or_str)
        else:
            self.wordforms = wordforms_or_str

        # slots
        # self.slots = [ParseSlot(slot) for slot in self.wordforms.slots]
        # self.slots = self.wordforms.slots

        # scansion
        if not scansion:
            scansion = get_iambic_parse(len(self.wordforms.slots))
        if type(scansion) == str:
            scansion = split_scansion(scansion)
        self.positions_ls = copy(scansion)

        # divide positions
        self.line = parent
        self.is_bounded = is_bounded
        self.bounded_by = [] if not bounded_by else [x for x in bounded_by]
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False
        self.parse_rank = rank
        # self.violset=Multiset()
        self.num_slots_positioned = 0
        self._line_num = line_num
        self._stanza_num = stanza_num
        self._line_txt = line_txt
        if not positions:
            super().__init__(children=[], parent=parent)
            for mpos_str in self.positions_ls:
                self.extend(mpos_str)
        else:
            super().__init__(children=positions, parent=parent)
        self.children = self.positions
        self.init()

    @property
    def line_num(self):
        return self.line.num if self.line else self._line_num

    @property
    def stanza_num(self):
        return self.stanza.num if self.line else self._stanza_num

    def init(self):
        for pos in self.positions:
            pos.parse = self
            pos.init()

    def to_json(self, fn=None):
        return to_json(
            {
                "_class": self.__class__.__name__,
                **self.attrs,
                "children": [pos.to_json() for pos in self.positions],
                "_wordforms": self.wordforms.to_json(),
                "_meter": self.meter_obj.to_json(),
                "is_bounded": self.is_bounded,
                "bounded_by": list(self.bounded_by),
            },
            fn=fn,
        )

    @staticmethod
    def from_json(json_d, line=None):
        from .lines import Line

        wordforms = from_json(json_d["_wordforms"])
        if line:
            if type(line) == Text:
                line = line.stanzas[json_d["stanza_num"] - 1].lines[
                    json_d["line_num"] - 1
                ]
            elif type(line) == Stanza:
                line = line.lines[json_d["line_num"] - 1]
            elif type(line) != Line:
                raise Exception(f"what is {line}?")
            wordforms = line.match_wordforms(wordforms)
        meter = from_json(json_d["_meter"])
        positions = [from_json(d) for d in json_d["children"]]
        slots = [slot for pos in positions for slot in pos.slots]
        sylls = [syll for word in wordforms for syll in word.children]
        assert len(slots) == len(sylls)
        for syll, slot in zip(sylls, slots):
            slot.unit = syll
        return Parse(
            wordforms,
            positions=positions,
            parent=line,
            meter=meter,
            is_bounded=json_d["is_bounded"],
            bounded_by=json_d["bounded_by"],
            rank=json_d["rank"],
            line_num=json_d["line_num"],
            stanza_num=json_d["stanza_num"],
        )

    @property
    def slots(self):
        return [slot for mpos in self.positions for slot in mpos.slots]

    @property
    def is_complete(self):
        return len(self.slots) == len(self.syllables)

    def extend(self, mpos_str: str):  # ww for 2 slots, w for 1, etc
        slots = []
        mval = mpos_str[0]
        if self.positions and self.positions[-1].meter_val == mval:
            # logger.warning(f'cannnot extend because last position is also {mval}')
            return None

        for i, x in enumerate(mpos_str):
            slot_i = self.num_slots_positioned
            try:
                slot = self.wordforms.slots[slot_i]
            except IndexError:
                # logger.warning('cannot extend further, already taking up all syllable slots')
                return None

            slots.append(ParseSlot(slot, num=slot_i + 1))
            self.num_slots_positioned += 1

        mpos = ParsePosition(
            meter_val=mval, children=slots, parent=self, num=len(self.positions) + 1
        )
        self.positions.append(mpos)
        self.constraint_viols  # init and bound
        return self

    @property
    def violset(self):
        s = Multiset()
        for mpos in self.positions:
            s.update(mpos.violset)
        return s

    def __copy__(self):
        new = Parse(
            wordforms_or_str=self.wordforms,
            scansion=self.positions_ls,
            meter=self.meter,
            parent=self.parent,
            positions=[copy(mpos) for mpos in self.positions],
        )
        new._attrs = copy(self._attrs)
        new.is_bounded = self.is_bounded
        new.num_slots_positioned = self.num_slots_positioned
        # new.violset = copy(self.violset)
        return new

    def branch(self):
        if self.is_bounded:
            return []
        if not self.positions:
            logger.error("needs to start with some positions")
            return
        mval = self.positions[-1].meter_val
        otypes = self.meter.get_pos_types(self.wordforms.num_sylls)
        otypes = [x for x in otypes if x[0] != mval]
        o = [copy(self).extend(posstr) for posstr in otypes]
        o = [x for x in o if x is not None]
        o = o if o else [self]
        o = [p for p in o if not p.is_bounded]
        return o

    @property
    def is_complete(self):
        return self.num_slots_positioned == len(self.wordforms.slots)

    @property
    def sort_key(self):
        return (
            self.stanza_num,
            self.line_num,
            int(bool(self.is_bounded)),
            self.score,
            self.positions[0].is_prom if self.positions else 10,
            self.average_position_size,
            self.num_stressed_sylls,
            self.meter_ints,
            self.stress_ints,
        )

    @cached_property
    def constraints(self):
        return self.meter.constraints + self.meter.categorical_constraints

    @cached_property
    def constraint_d(self):
        return dict((c.__name__, c) for c in self.constraints)

    @cached_property
    def categorical_constraint_d(self):
        return dict((c.__name__, c) for c in self.meter.categorical_constraints)

    # @profile

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    # @profile
    def __eq__(self, other):
        # logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        # return not (self<other) and not (other<self)
        return self is other

    def can_compare(self, other, min_slots=4):
        if (self.stanza_num, self.line_num) != (other.stanza_num, other.line_num):
            return False

        if min_slots and self.num_slots_positioned < min_slots:
            return False

        if self.is_complete and other.is_complete:
            return True

        if self.num_slots_positioned != other.num_slots_positioned:
            return False

        return True

    @cached_property
    def txt(self):
        return " ".join(m.txt for m in self.positions)

    # def __repr__(self):
    # attrstr=get_attr_str(self.attrs)
    # parse=self.txt
    # preattr=f'({self.__class__.__name__}: {parse})'
    # return f'{preattr}{attrstr}'

    @property
    def num_stressed_sylls(self):
        return len(
            [slot for mpos in self.positions for slot in mpos.slots if slot.is_stressed]
        )

    @property
    def num_sylls(self):
        return len(self.slots)

    @property
    def num_words(self):
        return len(self.wordforms)

    @property
    def num_peaks(self):
        return len([mpos for mpos in self.positions if mpos.is_prom])

    @property
    def is_rising(self):
        if not self.positions:
            return
        # return not self.positions[0].is_prom
        try:
            if self.nary_feet == 3:
                if self.slots[3].is_prom:
                    return False  # swws
                else:
                    return True  # wssw
            elif self.nary_feet == 2:
                if self.slots[3].is_prom:
                    return True  # wsws
                else:
                    return False  # swsw
        except (IndexError, AttributeError):
            pass
        return not self.positions[0].is_prom

    @property
    def nary_feet(self):
        return int(np.median(self.foot_sizes))

    @property
    def feet(self):
        if self.num_positions == 1:
            feet = [self.positions[0].meter_str]
        else:
            feet = []
            for i in range(1, self.num_positions, 2):
                pos1, pos2 = self.positions[i - 1], self.positions[i]
                feet.append(pos1.meter_str + pos2.meter_str)
        return feet

    @property
    def foot_counts(self):
        return Counter(self.feet)

    @property
    def foot_sizes(self):
        return [len(ft) for ft in self.feet]

    @property
    def num_positions(self):
        return len(self.positions)

    @property
    def foot_type(self):
        if self.nary_feet == 2:
            return "iambic" if self.is_rising else "trochaic"
        elif self.nary_feet == 3:
            return "anapestic" if self.is_rising else "dactylic"
        logger.error("foot type?")
        return ""

    @property
    def is_iambic(self):
        return self.foot_type == "iambic"

    @property
    def is_trochaic(self):
        return self.foot_type == "trochaic"

    @property
    def is_anapestic(self):
        return self.foot_type == "anapestic"

    @property
    def is_dactylic(self):
        return self.foot_type == "dactylic"

    @property
    # @profile
    def average_position_size(self):
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    # @profile
    def attrs(self):
        return {
            "stanza_num": force_int(self.stanza_num),
            "line_num": force_int(self.line_num),
            "line_txt": self.line_txt,
            **self._attrs,
            "txt": self.txt,
            "rank": self.parse_rank,
            "meter": self.meter_str,
            "stress": self.stress_str,
            "score": self.score,
            "ambig": self.ambig,
            "is_bounded": int(bool(self.is_bounded)),
        }

    @property
    def line_txt(self):
        return self.line.txt if self.line else self._line_txt

    @property
    def ambig(self):
        return (
            self.line._parses.num_unbounded if self.line and self.line._parses else None
        )

    @property
    # @profile
    def constraint_viols(self):
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d = {}
        nans = [np.nan for _ in range(len(self.slots))]
        catcts = set(self.categorical_constraint_d.keys())
        for cname, constraint in self.constraint_d.items():
            d[cname] = cscores = [
                x for score_d in scores for x in score_d.get(cname, nans)
            ]
            if cname in catcts and any(cscores):
                logger.debug(
                    f"Bounding {self.meter_str} because violates categorical constraint {cname}"
                )
                self.is_bounded = True
        return d

    @property
    # @profile
    def constraint_scores(self):
        return {cname: safesum(cvals) for cname, cvals in self.constraint_viols.items()}

    @property
    # @profile
    def score(self):
        return safesum(self.constraint_scores.values())

    # return a list of all slots in the parse

    @property
    # @profile
    def meter_str(self, word_sep=""):
        return "".join(
            "+" if mpos.is_prom else "-"
            for mpos in self.positions
            for slot in mpos.slots
        )

    @property
    def meter_ints(self, word_sep=""):
        return tuple(
            int(mpos.is_prom) for mpos in self.positions for slot in mpos.slots
        )

    @property
    def stress_ints(self, word_sep=""):
        return tuple(int(slot.is_stressed) for slot in self.slots)

    @property
    # @profile
    def stress_str(self, word_sep=""):
        return "".join(
            "+" if slot.is_stressed else "-"
            for mpos in self.positions
            for slot in mpos.slots
        ).lower()

    # return a representation of the bounding relation between self and parse
    # @profile
    def bounding_relation(self, parse):
        selfviolset = self.violset
        parseviolset = parse.violset
        if selfviolset < parseviolset:
            return Bounding.bounds
        elif selfviolset > parseviolset:
            return Bounding.bounded
        elif selfviolset == parseviolset:
            return Bounding.equal
        else:
            return Bounding.unequal

    def bounds(self, parse):
        return self.bounding_relation(parse) == Bounding.bounds

    def _repr_html_(self):
        return self.to_html(as_str=True, blockquote=True)

    @cached_property
    def html(self):
        return self.to_html()

    def to_html(self, as_str=False, css=HTML_CSS, blockquote=True):
        assert self.line
        out = self.line.to_html(as_str=True, css=css)
        if blockquote:
            reprstr = get_attr_str(self.attrs, bad_keys={"txt", "line_txt"})
            out += f'<div class="miniquote">⎿ {reprstr}</div>'
        return to_html(out, as_str=as_str)

    @cached_property
    def wordtoken2slots(self):
        wordtokend = defaultdict(list)
        for slot in self.slots:
            wordtokend[slot.unit.wordtoken].append(slot)
        return wordtokend

    def stats_d(self, norm=None):
        if norm is None:
            odx1 = self.stats_d(norm=False)
            odx2 = self.stats_d(norm=True)
            for k in list(odx2.keys()):
                if k[0] == "*":
                    odx2[k + "_norm"] = odx2.pop(k)
            return {**odx1, **odx2}

        odx = {**self.attrs}
        cnames = [f.__name__ for f in self.meter.constraints]
        odx["num_sylls"] = self.num_sylls
        odx["num_words"] = self.num_words

        for cname in cnames:
            odx[f"*{cname}"] = (
                np.mean([slot.viold[cname] for slot in self.slots])
                if norm
                else self.constraint_scores[cname]
            )
        viols = [int(slot.has_viol) for slot in self.slots]
        scores = [int(slot.score) for slot in self.slots]
        odx["*total_sylls"] = np.mean(viols) if norm else sum(viols)
        odx["*total"] = np.mean(scores) if norm else sum(scores)
        return odx

    def get_df(self, *x, **y):
        df = super().get_df(*x, **y)
        df.columns = [
            c.replace("meterslot_syll_", "syll_").replace(
                "meterslot_wordtoken_", "wordtoken_"
            )
            for c in df
        ]
        return setindex(df.reset_index(), DF_INDEX).sort_index()


class ParsePosition(Entity):
    prefix = "meterpos"

    # @profile

    # meter_val represents whether the position is 's' or 'w'
    def __init__(self, meter_val: str, children=[], parent=None, **kwargs):
        self.viold = (
            {}
        )  # dict of lists of viols; length of these lists == length of `slots`
        self.violset = set()  # set of all viols on this position
        self.slots = children
        self.parse = parent
        super().__init__(
            meter_val=meter_val,
            children=children,
            parent=parent,
            num_slots=len(self.slots),
            **kwargs,
        )
        if self.parse:
            self.init()

    def init(self):
        assert self.parse
        if any(not slot.unit for slot in self.slots):
            print(self.slots)
            print([slot.__dict__ for slot in self.slots])
            raise Exception
        for cname, constraint in self.parse.constraint_d.items():
            slot_viols = [int(bool(vx)) for vx in constraint(self)]
            assert len(slot_viols) == len(self.slots)
            self.viold[cname] = slot_viols
            if any(slot_viols):
                self.violset.add(cname)
            for viol, slot in zip(slot_viols, self.slots):
                slot.viold[cname] = viol

    def __copy__(self):
        new = ParsePosition(
            self.meter_val,
            children=[copy(slot) for slot in self.children],
            parent=self.parent,
        )
        new.viold = copy(self.viold)
        new.violset = copy(self.violset)
        new._attrs = copy(self._attrs)
        return new

    def to_json(self):
        return super().to_json(meter_val=self.meter_val)

    @cached_property
    def attrs(self):
        return {
            **self._attrs,
            "num": self.num,
            # **{k:sum(v) for k,v in self.viold.items()}
        }

    @cached_property
    # @profile
    def constraint_viols(self):
        return self.viold

    @cached_property
    def constraint_scores(self):
        return {k: sum(v) for k, v in self.constraint_viols.items()}

    @cached_property
    # @profile
    def constraint_set(self):
        return self.violset

    @cached_property
    def is_prom(self):
        return self.meter_val == "s"

    @cached_property
    def txt(self):
        token = ".".join([slot.txt for slot in self.slots])
        token = token.upper() if self.is_prom else token.lower()
        return token

    @cached_property
    def meter_str(self):
        return self.meter_val * self.num_slots

    @cached_property
    def num_slots(self):
        return len(self.slots)


class ParseSlot(Entity):
    prefix = "meterslot"

    # @profile

    def __init__(
        self, unit: "Syllable" = None, parent=None, children=[], viold={}, **kwargs
    ):
        # print(unit,parent,children,viold,kwargs)
        if unit is None and children:
            assert len(children) == 1
            unit = children[0]

        self.unit = unit
        self.viold = {**viold}
        super().__init__(children=[], parent=parent, **kwargs)

    def __copy__(self):
        new = ParseSlot(unit=self.unit)
        new.viold = copy(self.viold)
        new._attrs = copy(self._attrs)
        return new

    def to_json(self):
        d = super().to_json(unit=self.unit.to_hash(), viold=self.viold)
        d.pop("children")
        return d

    @cached_property
    def violset(self):
        return {k for k, v in self.viold.items() if v}

    @cached_property
    def num_viols(self):
        return len(self.violset)

    @cached_property
    def constraint_scores(self):
        return self.viold

    @cached_property
    def meter_val(self):
        return self.parent.meter_val

    @cached_property
    def is_prom(self):
        return self.parent.is_prom

    @cached_property
    def wordform(self):
        return self.unit.parent

    @cached_property
    def syll(self):
        return self.unit

    @cached_property
    def is_stressed(self):
        return self.unit.is_stressed

    @cached_property
    def is_heavy(self):
        return self.unit.is_heavy

    @cached_property
    def is_strong(self):
        return self.unit.is_strong

    @cached_property
    def is_weak(self):
        return self.unit.is_weak

    @cached_property
    def score(self):
        return sum(self.viold.values())

    @cached_property
    def has_viol(self):
        return bool(self.score)

    @cached_property
    def txt(self):
        o = self.unit.txt
        return o.upper() if self.is_prom else o.lower()

    @cached_property
    def i(self):
        return self.parent.parent.slots.index(self)

    @cached_property
    def attrs(self):
        return {
            **{
                k: v
                for k, v in self.unit.prefix_attrs.items()
                if k.split("_")[0] in {"wordtoken", "syll"}
            },
            **self._attrs,
            "num": self.num,
            **self.viold,
        }



# class representing the potential bounding relations between to parses
class Bounding:
    bounds = 0  # first parse harmonically bounds the second
    bounded = 1  # first parse is harmonically bounded by the second
    equal = 2  # the same constraint violation scores
    unequal = 3  # unequal scores; neither set of violations is a subset of the other


def get_iambic_parse(nsyll):
    o = []
    while len(o) < nsyll:
        x = "w" if not o or o[-1] == "s" else "s"
        o.append(x)
    return o
