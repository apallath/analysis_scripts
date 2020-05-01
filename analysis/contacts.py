"""Plot number of contacts and fraction of native contacts with time

Units:
- length: A
- time: ps

@Author: Akash Pallath

TODO:   Mean and CI plot for appended plots
"""
from analysis.timeseries import TimeSeries

import numpy as np
import matplotlib.pyplot as plt
import MDAnalysis as mda
import MDAnalysis.lib.distances #for fast distance matrix calculation

class Contacts(TimeSeries):
    def __init__(self):
        super().__init__()
        self.parser.add_argument("structf", help="Structure file (.gro)")
        self.parser.add_argument("trajf", help="Compressed trajectory file (.xtc)")
        self.parser.add_argument("-distcutoff", help="Distance cutoff for contacts, in A (default = 4.5 A)")
        self.parser.add_argument("-refcontacts", help="Reference number of contacts for fraction (default = mean)")
        self.parser.add_argument("-skip", help="Number of frames to skip between analyses")
        self.parser.add_argument("--verbose", action='store_true', help="Output progress of contacts calculation")

    # Read arguments into member variables
    def read_args(self):
        super().read_args()
        self.structf = self.args.structf
        self.trajf = self.args.trajf

        self.refcontacts = self.args.refcontacts
        if self.refcontacts is not None:
            self.refcontacts = float(self.refcontacts)

        self.skip = self.args.skip
        if self.skip is not None:
            self.skip = int(self.skip)

        self.verbose = self.args.verbose
        self.distcutoff = self.args.distcutoff
        if self.distcutoff is not None:
            self.distcutoff = float(self.distcutoff)
        else:
            self.distcutoff = 4.5

        # Prepare system from args
        self.u = mda.Universe(self.structf, self.trajf)
        self.refu = mda.Universe(self.structf)
        if self.skip is None:
            self.skip = 1

    """ (deprecated)
    # Reference contacts calculation
    def calc_refcontacts(self):
        side_heavy_sel = "protein and not(name N or name CA or name C or name O or name OC1 or name OC2 or type H)"

        refprotein = self.refu.select_atoms("protein")

        nres = len(refprotein.residues)
        box = self.refu.dimensions

        refcontacts = 0

        for i in range(nres):
            heavy_side_i = refprotein.residues[i].atoms.select_atoms(side_heavy_sel)
            heavy_side_j = refprotein.residues[i+4:].atoms.select_atoms(side_heavy_sel)
            da = mda.lib.distances.distance_array(heavy_side_i.positions, heavy_side_j.positions, box)
            refcontacts += np.count_nonzero(da < self.distcutoff)

        self.refcontacts = refcontacts
    """

    # Contacts analysis along trajectory
    def calc_trajcontacts(self):
        side_heavy_sel = "protein and not(name N or name CA or name C or name O or name OC1 or name OC2 or type H)"

        protein = self.u.select_atoms("protein")

        nres = len(protein.residues)

        step = 0
        contacts = []

        for ts in self.u.trajectory[0::self.skip]:
            box = ts.dimensions
            ncontacts = 0

            for i in range(nres):
                heavy_side_i = protein.residues[i].atoms.select_atoms(side_heavy_sel)
                heavy_side_j = protein.residues[i+4:].atoms.select_atoms(side_heavy_sel)
                da = mda.lib.distances.distance_array(heavy_side_i.positions, heavy_side_j.positions, box)
                ncontacts += np.count_nonzero(da < self.distcutoff)
            # Print progress
            if self.verbose:
                print("Step = {}, time = {} ps, contacts = {}".format(step*self.skip + 1,ts.time,ncontacts))

            contacts.append([ts.time, ncontacts])
            step += 1

        self.contacts = np.array(contacts)

    """call"""
    def __call__(self):
        """Contacts along trajectory plot"""
        if self.replot:
            replotdata = np.load(self.replotpref + "_contacts.npy")
            self.contacts = np.transpose(replotdata)
        else:
            # Calculate contacts along trajectory
            self.calc_trajcontacts()

        contacts = self.contacts[:,1]
        t = self.contacts[:,0]
        mean, serr, ci_95_low, ci_95_high = self.average(t, contacts, self.avgstart, self.avgend)

        if self.refcontacts is None:
            self.refcontacts = mean

        # Plot number of contacts
        fig, ax = plt.subplots()
        ax.plot(t,contacts)
        # Plot mean and errors
        meanline = mean*np.ones(len(t))
        ci_low_line = ci_95_low*np.ones(len(t))
        ci_high_line = ci_95_high*np.ones(len(t))
        ax.plot(t,meanline,color='green')
        ax.fill_between(t,ci_low_line,ci_high_line,alpha=0.2,facecolor='green',edgecolor='green')
        plt.title('Mean = {:.2f}\n95% CI = [{:.2f}, {:.2f}]'.format(mean, ci_95_low, ci_95_high))
        # Plot properties
        ax.set_xlabel("Time (ps)")
        ax.set_ylabel("Number of contacts")
        self.save_figure(fig,suffix="contacts")
        self.save_timeseries(self.contacts[:,0], self.contacts[:,1], label="contacts")
        if self.show:
            plt.show()

        # Plot fraction of contacts
        fig, ax = plt.subplots()
        ax.plot(t, contacts/self.refcontacts)
        # Plot mean and errors
        meanline = mean/self.refcontacts*np.ones(len(t))
        ci_low_line = ci_95_low/self.refcontacts*np.ones(len(t))
        ci_high_line = ci_95_high/self.refcontacts*np.ones(len(t))
        ax.plot(t,meanline,color='green')
        ax.fill_between(t,ci_low_line,ci_high_line,alpha=0.2,facecolor='green',edgecolor='green')
        plt.title('95% CI = [{:.2f}, {:.2f}]'.format(ci_95_low/self.refcontacts, ci_95_high/self.refcontacts))
        # Plot properties
        ax.set_xlabel("Time (ps)")
        ax.set_ylabel("Fraction of contacts")
        self.save_figure(fig,suffix="frac_contacts")
        self.save_timeseries(self.contacts[:,0], self.contacts[:,1], label="contacts")
        if self.show:
            plt.show()

        if self.apref is not None:
            tcp = np.load(self.apref + "_contacts.npy")
            tp = tcp[0,:]
            contactsp = tcp[1,:]
            tn = tp[-1]+t

            #plot contacts time series
            fig, ax = plt.subplots()
            ax.plot(tp,contactsp,label=self.aprevlegend)
            ax.plot(tn,contacts,label=self.acurlegend)
            ax.set_xlabel("Time (ps)")
            ax.set_ylabel("Number of contacts")
            ax.legend()
            self.save_figure(fig,suffix="app_contacts")
            if self.show:
                plt.show()

            #plot fraction of contacts time series
            fig, ax = plt.subplots()
            ax.plot(tp,contactsp/self.refcontacts,label=self.aprevlegend)
            ax.plot(tn,contacts/self.refcontacts,label=self.acurlegend)
            ax.set_xlabel("Time (ps)")
            ax.set_ylabel("Fraction of contacts")
            ax.legend()
            self.save_figure(fig,suffix="app_frac_contacts")
            if self.show:
                plt.show()

warnings = "Proceed with caution: this script requires PBC-corrected protein structures!\n"

if __name__=="__main__":
    contacts = Contacts()
    contacts.read_args()
    startup_string = "#### Contacts ####\n" + warnings
    print(startup_string)
    contacts()
