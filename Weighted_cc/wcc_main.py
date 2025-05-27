from optparse import OptionParser
from Graphs import Graph
import CalLig as lig


class optParser():
    def __init__(self, fakeArgs):
        parser = OptionParser()
        parser.add_option('-f', '--file', dest='file', help='Input file containing pairwise energy data')
        parser.add_option('-r', '--ref', dest='ref',help='Reference molecule for calculating the energy for other molecules. Default: The first molecule in the data file',
                          default='')
        parser.add_option('-e', '--ref_ene', dest='ref_ene', help='Energy for the reference molecule. Default: 0.00',
                          default=0.00, type=float)
        parser.add_option('-o', '--output', dest='output', help='Output file name. Default: output.txt')
        if fakeArgs:
            self.option, self.args = parser.parse_args(fakeArgs)
        else:
            self.option, self.args = parser.parse_args()

if __name__ == '__main__':
    opts = optParser('')
    # fakeArgs = "-f bace_run1_0_with_w -r 3A -e -8.83 -p yes"  # only keep this for test purpose
    # opts = optParser(fakeArgs.strip().split())  # only keep this for test purpose
    if not opts.option.file:
        raise Exception("No input energy data!")
    g = Graph(opts.option.file)
    g.getAllCyles()
    if len(g.cycles)== 0:
        print("No cycle in this graph.")
        exit()
    g.iterateCycleClosure(minimum_cycles=2)
    node_map=lig.set_node_map(g)
    if not opts.option.ref.strip():
        opts.option.ref=g.V[0]
    try:
        ref_node = g.V.index(opts.option.ref)
    except ValueError as e:
        print("Check your args. Ref",opts.option.ref,"isn't in your input file!")
        exit()
    path_independent_error = lig.cal_node_path_independent_error(g.V, node_map)
    path_dependent_error, path = lig.cal_node_path_dependent_error(ref_node, g.V, node_map)
    mol_ene = lig.calcMolEnes(opts.option.ref_ene, g, path)
    lig.printMol(g.V,mol_ene,path_dependent_error,path_independent_error)
    lig.outputMol(g.V,mol_ene,opts.option.output)


