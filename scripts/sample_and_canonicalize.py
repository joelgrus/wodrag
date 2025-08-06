
import dspy

from wodrag.utils import sample_workouts


class ExtractMovements(dspy.Signature):
    """
    I will give you a bunch of workout descriptions, I want you to extract the unique movements from them.
    For example a movement could be something "pull up" or "clean and jerk" or "run".
    Please extract them as all lowercase strings, with no punctuation. Convert hyphens to spaces.
    Do not repeat movements. Movement names should be singular.
    ("pull up" not "pull ups", "clean and jerk" not "clean and jerks", "run" not "runs").
    """

    text: str = dspy.InputField(description="Text containing movement data.")
    movements: list[str] = dspy.OutputField(description="List of extracted movements.")


extractor = dspy.ChainOfThought(ExtractMovements)


if __name__ == "__main__":
    dspy.configure(lm=dspy.LM("openrouter/google/gemini-2.5-flash", max_tokens=100000))
    text = sample_workouts().join("\n\n")
    extracted = extractor(text=text)
    for _movement in sorted(extracted.movements):
        pass
