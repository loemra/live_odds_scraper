from packages.data.Match import Match


class MockMatcher:
    def __init__(self, inputs=[], db=None):
        self.inputs = inputs
        self.db = db

    def match(self, to_be_matched, potential_matches):
        def _match():
            if to_be_matched is None and None in potential_matches:
                return potential_matches.index(None)
            if len(self.inputs) > 0:
                print(
                    f"{to_be_matched} MATCHED {potential_matches} @"
                    f" {self.inputs[0]}"
                )
                return self.inputs.pop(0)

            if len(potential_matches) == 0:
                return None

            index_or_none = input(
                f"\n{to_be_matched}\nPOTENTIAL MATCHES:"
                f" {potential_matches}\nENTER EITHER A ZERO-BASED INDEX OR"
                " NONE: "
            )

            if index_or_none.lower() == "none":
                return None
            return int(index_or_none)

        res = _match()
        if self.db is not None:
            matches = []
            for i, pm in enumerate(potential_matches):
                matches.append(
                    Match(to_be_matched, pm, res is not None and i == res)
                )
            self.db.record_match(matches)
        return res
