"""
TODO: Checkout dexpy and statsmodels
https://statease.github.io/dexpy/
https://www.statsmodels.org/dev/index.html

doepydoc: https://doepy.readthedocs.io/en/latest/

"""


from doepy import build
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import LabelEncoder
import sys

# if len(sys.argv) < 2:
#     sys.exit("Usage: python doe.py [full | frac <res> | fill | cc[cif] ]")

class DOE():
    def __init__(self, factors=None, levels=None, type=None, design=None):
        self._factors = factors
        self._levels = levels
        self._type = type
        self._design = design
    
    @property
    def factors(self):
        return self._factors
    
    @factors.setter
    def factors(self, factors):
        ... # validation
        self._factors = factors

    @property
    def levels(self):
        return self._levels
    
    @levels.setter
    def levels(self, levels):
        ... # validation
        self._levels = levels

    @property
    def type(self):
        return self._type
    
    @type.setter
    def type(self, type):
        if type in ["full", "fill", "boxb", "frac", "ccc", "cci", "ccf"]:
            self._type = type
        else: 
            sys.exit(f"Invalid DOE type: '{type}'")


def main(factors, type=None, plot=None):
    # factors = {
    #     "Pressure": [40, 70],
    #     "Temperature": [290, 350],
    #     "Flow rate": [0.2, 0.4],
    #     #"Time": [0, 4, 8],
    #     #"Tests": ["low", "med", "high"]
    # }
    my_doe = DOE(factors.keys(), factors.values(), type=type)
    # print(my_doe.factors, my_doe.levels, my_doe.type, sep="\n")

    doe = pd.DataFrame({}) # initializes an empty dataframe to prevent printing nothing later on

    if type == "full":
        doe = full_factorial(**factors)
    elif type == "fill":
        doe = space_filling_lhs(**factors)
    elif type == "boxb":
        doe = box_benkhen(**factors)
    elif type == "frac":
        doe = fract_factorial(**factors, res=2)
    elif type == "ccc" or type == "cci" or type == "ccf":
        doe = central_composite(face=type, **factors)
    
    if not doe.empty :
        # print(doe)
        if plot == "3d":  
            try:        
                plot3d(doe, type)
            except:
                print("3d plot not possible, try another plot type")
        elif plot == "scatter":
            try:
                scatterplot(doe, type)
            except Exception as err:
                print(f'Scatter Plot: {err}')

        return doe.to_dict()


def full_factorial(**kwargs):
    df = build.full_fact(kwargs)
    df.index = df.index + 1
    return df

def fract_factorial(res, **kwargs):
    df = build.frac_fact_res(kwargs, res=res)
    df.index = df.index + 1
    return df

def central_composite(face='ccf', **kwargs):
    """
    Box-Wilson Design
    ==================
    face = ccf: center-faced
    face = cci: center-inscribed
    face = ccc: center-circumscribed
    """
    df = build.central_composite(kwargs, face=face)
    df.index = df.index + 1
    return df

def space_filling_lhs(**kwargs):
    n_runs = pow(2, len(kwargs))
    df = build.space_filling_lhs(kwargs, num_samples=n_runs)
    df.index = df.index + 1
    return df

def box_benkhen(**kwargs):
    df = build.box_behnken(kwargs)
    df.index = df.index + 1
    return df

def plot3d(df, type):
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(111, projection='3d')
    args = [df.iloc[:, n] for n in range(len(df.columns))]
    ax.scatter3D(
        *args[0:3],
        s=50 # size of point
    )
    ax.set_xlabel(df.columns[0])  # Use column names for labels
    ax.set_ylabel(df.columns[1])
    ax.set_zlabel(df.columns[2])
    ax.set_title(f'3D Plot for {df.columns[0]}, {df.columns[1]}, and {df.columns[2]}\n Type: {type}')
    ax.view_init(30, 125)
    plt.show()

def scatterplot(df, type):
    # Apply label encoding to object (categorical) columns
    label_encoder = LabelEncoder()
    df = df.apply(lambda col: label_encoder.fit_transform(col) if col.dtype != 'object' else col)
    
    g = sns.pairplot(df, 
                    # hue=df.columns[0],
                    corner=True,
                    diag_kind='kde',
                    # palette='dark',
                    # markers=[11,10],
                    # height= 2.5, aspect=1.2
                    )
    x = len(df.columns) + 1.5
    y = len(df.columns) + 1.5
    g.fig.set_size_inches(x,y)

    # Remove the unnecessary elements in the diagonal plots
    for i, ax in enumerate(g.diag_axes):
        ax.set_visible(True)
        ax.text(0.5, 0.5, df.columns[i], transform=ax.transAxes,
                ha='center', va='center', fontweight='bold')

    # Get Factors list
    factors = [factor for factor in df.columns.tolist()]
    g.fig.suptitle(f'Scatter Plot for {factors}\n Type: {type}',
                   verticalalignment= 'top',
                   horizontalalignment= 'left',
                   fontsize=12, x=0.01)
    # Adjust the size of the axis labels (tick labels)
    for ax in g.axes.flat:
        if ax:
            ax.xaxis.set_tick_params(labelsize=8)
            ax.yaxis.set_tick_params(labelsize=8)
            ax.set_xlabel(ax.get_xlabel(), fontsize=9)
            ax.set_ylabel(ax.get_ylabel(), fontsize=9)
            # ax.spines['top'].set_visible(True)
            # ax.spines['right'].set_visible(True)

    # sns.move_legend(g, "upper right", bbox_to_anchor=(0.95,0.95))
    plt.tight_layout(pad=1.2)
    plt.show()


if __name__ == "__main__":
    main()
