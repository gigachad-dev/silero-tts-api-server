import torch
from pathlib import Path
from io import BytesIO

# fixes import package error on Mac
# https://github.com/snakers4/silero-models/discussions/104
torch.backends.quantized.engine = "qnnpack"

torch.set_num_threads(4)
device = torch.device("cpu")


class TTS:
    def __init__(self):
        self.models = {}
        self.speakers = {}
        self.model_by_speaker = {}

        for model_path in Path("models").glob("*.pt"):
            self._load_model(model_path)

    def generate(self, text, speaker, sample_rate):
        assert text != "random"

        model = self.model_by_speaker.get(speaker)
        assert model is not None, f"speaker {speaker} not found"

        return self._generate_audio(model, text, speaker, sample_rate)

    def _load_model(self, model_path: Path):
        package = torch.package.PackageImporter(model_path)
        model = package.load_pickle("tts_models", "model")
        model.to(device)
        
        language = model_path.stem[3:]
        self.models.update({language: model})

        self._load_speakers(model, language)

    def _load_speakers(self, model, language):
        if "random" in model.speakers:
            model.speakers.remove("random")

        self.speakers.update({language: model.speakers})
        for speaker in model.speakers:
            self.model_by_speaker[speaker] = model

    def _generate_audio(self, model, text, speaker, sample_rate):
        audio = model.apply_tts(text=text, speaker=speaker, sample_rate=sample_rate)

        buffer = BytesIO()
        model.write_wave(
            buffer,
            audio=(audio * 32767).numpy().astype("int16"),
            sample_rate=sample_rate,
        )
        buffer.seek(0)

        return buffer.read()


tts = TTS()
