import os
from spicelib.editor.asc_editor import AscEditor
from spicelib import SimRunner
from spicelib.simulators.ltspice_simulator import LTspice
from spicelib.sim.tookit.montecarlo import Montecarlo

script_dir = os.path.dirname(os.path.abspath(__file__))
circuit = AscEditor(os.path.join(script_dir, 'transitorio.asc'))
runner = SimRunner(output_folder=os.path.join(script_dir, 'mc_output'), simulator=LTspice)
mc = Montecarlo(circuit, runner)
mc.set_tolerance('R1', 0.05)
mc.set_tolerance('R2', 0.05)
mc.set_tolerance('R3', 0.05)
mc.set_tolerance('C1', 0.10)
mc.set_tolerance('L1', 0.00)

mc.run_analysis(num_runs=100)