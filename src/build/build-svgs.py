import os
from pathlib import Path

registerJsonsDir = Path(os.path.realpath(__file__)).parent.parent.joinpath("ps4-reg-desc")
registerSvgsDir = Path(os.path.realpath(__file__)).parent.parent.joinpath("svgs")
for filename in registerJsonsDir.rglob("*.json"):
    os.system("npx bit-field --vspace 64 -i \"" + str(filename) + "\" > \"" + str(registerSvgsDir.joinpath(filename.parent.name + "/" + filename.name.split(".json")[0] + ".svg")) + '"')
