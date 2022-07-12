import os
from pathlib import Path
import subprocess
import shutil

# Asynchronously execute the bit-field program to generate all the SVGs
registerJsonsDir = Path(os.path.realpath(__file__)).parent.parent.joinpath("ps4-reg-desc")
registerSvgsDir = Path(os.path.realpath(__file__)).parent.parent.joinpath("svgs")
processes = []
for filename in registerJsonsDir.rglob("*.json"):
    svgPath = str(registerSvgsDir.joinpath(
            filename.parent.name + "/" + 
            filename.name.split(".json")[0] + ".svg"))
    if (os.path.exists(svgPath)): 
        os.remove(svgPath)
        
    svgFile = open(svgPath, "a")
    processes.append((subprocess.Popen(
        [shutil.which("npx"), 
        "bit-field", 
        "--lanes", 
        "1",
        "--vspace", 
        "80",
        "--hspace", 
        "1124",
        "-i",
        str(filename)], stdout=svgFile, text=True), svgFile))
for (process, svgFile) in processes:
    process.wait()
    svgFile.close()
