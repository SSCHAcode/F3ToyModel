import numpy as np

import ase
import ase.units
import ase.calculators.calculator as calc

import cellconstructor as CC 
import cellconstructor.Structure


# Import the fortran libraries
import fforceslibs as  f3libs



class ToyModelCalculator(calc.Calculator):

    def __init__(self, harmonic_dyn, type_cal = "pdhxx", *args, **kwargs):
        calc.Calculator.__init__(self, *args, **kwargs)

        # Type cal defines the kind of the force field to be used
        self.type_cal = type_cal

        # Setup what properties the calculator can load
        self.implemented_properties = ["energy", "forces"]

        # Prepare the variable specific for this calculator
        # This must be a CellConstructor Phonons
        self.harmonic_dyn = harmonic_dyn

        # The parameters
        # The second order force constant enhancement factor
        self.p2 = 0

        # The third and higher order coefficients
        # NOTE: ALL THE COEFFICIENTS ARE IN Ha units!  
        self.p3 = 0
        self.p4 = 0
        self.p5 = 0
        self.p6 = 0

        self.p3x = 0
        self.p4x = 0
        self.p4f = 0
        self.p4g = 0

        # No clue of what they are
        self.b = 0
        self.c = 0


        # We prepare the data for the faster submission inside the fortran arrays
        superdyn = self.harmonic_dyn.GenerateSupercellDyn(self.harmonic_dyn.GetSupercell())
        phi_sc = superdyn.dynmats[0]
        
        super_structure = self.harmonic_dyn.structure.generate_supercell(self.harmonic_dyn.GetSupercell())
        self.nat_sc = super_structure.N_atoms
        self.phi_sc_harmonic = np.zeros((3,3, self.nat_sc, self.nat_sc), order = "F", dtype = np.double)

        for i in range(self.nat_sc):
            for j in range(self.nat_sc):
                self.phi_sc_harmonic[:, :, i, j] = phi_sc[3*i:3*i+3, 3*j:3*j+3]
        
        self.at_sc = np.zeros((3,3), dtype = np.double, order = "F") 
        self.at_sc[:,:] = super_structure.unit_cell.T *  CC.Units.A_TO_BOHR

        self.tau_sc = np.zeros((3, self.nat_sc), dtype = np.double, order = "F")
        self.tau_sc[:,:] = super_structure.coords.T * CC.Units.A_TO_BOHR

        # Get the minimum distance between two atoms
        all_dists = [super_structure.get_min_dist(0, i) for i in range(1, super_structure.N_atoms)]
        nn_dist = np.min(all_dists) * CC.Units.A_TO_BOHR

        # Get the ITYP
        self.ityp_sc = super_structure.get_ityp() + 1

        # Assign the near neighbours
        self.nn_at, self.nn_vect = f3libs.assign_nn(self.tau_sc, self.at_sc,
                                                    self.ityp_sc,
                                                    nn_dist, self.nat_sc)

        # Assign the PM
        self.slv_idx = f3libs.assign_pm(self.nn_vect, self.nn_at, nn_dist)


        
    def calculate(self, atoms=None, *args, **kwargs):
        calc.Calculator.calculate(self, atoms, *args, **kwargs)


        # Here we implement the calculation on the atoms object
        structure = CC.Structure.Structure()
        structure.generate_from_ase_atoms(self.atoms)

        assert structure.N_atoms == self.nat_sc, "Error, the structure do not match the harmonic dyn given."

        # Get the vector of the displacements
        u_disp = np.zeros((1, self.nat_sc, 3), order = "F", dtype = np.double)
        u_disp[0, :, :] = structure.coords * CC.Units.A_TO_BOHR - self.tau_sc.T 

        # Perform the calculation
        forces, v = f3libs.get_forces_energies(self.phi_sc_harmonic / 2, u_disp, self.type_cal, self.ityp_sc, \
            self.at_sc, self.tau_sc, self.b, self.c, self.p2, self.p3, self.p4, self.p5, self.p6, \
                                               self.p4x, self.p3x, self.p4f, self.p4g,
                                               self.nn_at, self.nn_vect, self.slv_idx)
        
        forces *= 2# Ha -> Ry
        v *= 2 # Ha -> Ry

        # print("Calculated energy forces:")
        # f = np.zeros((self.nat_sc, 3), dtype = np.double)
        # energ = 0
        # for i in range(self.nat_sc):
        #     f[i, :] = 0
        #     for j in range(self.nat_sc):
        #         f[i,:] -= self.phi_sc_harmonic[:,:,i,j].dot(u_disp[0, j, :])
        #         energ += 0.5 * u_disp[0, i, :].dot(self.phi_sc_harmonic[:,:,i,j].dot(u_disp[0,j,:]))
        # # print("F PYTHON:")
        # # print(f)
        # # print("F FORTRAN:")
        # # print(forces)
        # # print("F expected:")
        # # ssdyn = self.harmonic_dyn.GenerateSupercellDyn(self.harmonic_dyn.GetSupercell())
        # # ff,ee = ssdyn.get_energy_forces(structure)

        # print("Energy python:", energ, " FORTRAN:", v)
        
        
        # The energy is in [Ry] and the force is in Ry/bohr
        # Convert them in [eV] and [eV/
        v *= ase.units.Ry
        forces *= ase.units.Ry / CC.Units.BOHR_TO_ANGSTROM

        

        self.results = {"energy": v[0], "forces": forces[0,:,:]}
