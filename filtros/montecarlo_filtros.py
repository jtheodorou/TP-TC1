import os
from spicelib.editor.asc_editor import AscEditor
from spicelib import SimRunner
from spicelib.simulators.ltspice_simulator import LTspice
from spicelib.sim.tookit.montecarlo import Montecarlo

script_dir = os.path.dirname(os.path.abspath(__file__))
circuit = AscEditor(os.path.join(script_dir, 'fig5.asc'))
runner1 = SimRunner(output_folder=os.path.join(script_dir, 'mc_full'), simulator=LTspice)
mc1 = Montecarlo(circuit, runner1)
mc1.set_tolerance('R1', 0.05)
mc1.set_tolerance('C1', 0.10)
mc1.set_tolerance('L1', 0.10)

mc1.run_analysis(num_runs=100)

runnerC = SimRunner(output_folder=os.path.join(script_dir, 'mc_C'), simulator=LTspice)
mcC = Montecarlo(circuit, runnerC)
mcC.set_tolerance('C1', 0.10)

mcC.run_analysis(num_runs=100)

runnerL = SimRunner(output_folder=os.path.join(script_dir, 'mc_L'), simulator=LTspice)
mcL = Montecarlo(circuit, runnerL)
mcL.set_tolerance('L1', 0.10)

mcL.run_analysis(num_runs=100)

runnerLC = SimRunner(output_folder=os.path.join(script_dir, 'mc_LC'), simulator=LTspice)
mcLC = Montecarlo(circuit, runnerLC)
mcLC.set_tolerance('L1', 0.10)
mcLC.set_tolerance('C1', 0.10)

mcLC.run_analysis(num_runs=100)