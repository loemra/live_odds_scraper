class MockMatcher:
    def __init__(self, inputs=[]):
        self.inputs = inputs

    def match(self, to_be_matched, potential_matches):
        if len(self.inputs) > 0:
            print(
                f"{to_be_matched} MATCHED {potential_matches} @"
                f" {self.inputs[0]}"
            )
            return self.inputs.pop(0)

        index_or_none = input(
            f"\n{to_be_matched}\nPOTENTIAL MATCHES:"
            f" {potential_matches}\nENTER EITHER A ZERO-BASED INDEX OR NONE: "
        )

        if index_or_none.lower() == "none":
            return None
        return int(index_or_none)
