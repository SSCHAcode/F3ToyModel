project('F3ToyModel',
  ['c', 'fortran'],
  version: '1.1',
  license: 'GPL',
  meson_version: '>= 1.1.0', # <- set min version of meson.
  default_options : [
        'warning_level=1',
        'buildtype=release',
        'fortran_args=-O2',
        'fortran_args=-cpp'
    ]
    )

# --- Compilation options ---
use_mkl = get_option('use_mkl')

# --- System and Python Dependencies ---
# Find the necessary installations
py = import('python').find_installation(pure: false)
py_dep = py.dependency()
fc = meson.get_compiler('fortran')

# Additional dependencies

# The LAPACK and BLAS libraries are essential for Fortran matrix operations.
#lapack_dep = dependency('lapack')
#blas_dep = dependency('blas')
openblas_dep = dependency('openblas', required: false)
if use_mkl
  mkl_dep = dependency('mkl', required: true)
  blas_dep = mkl_dep
  lapack_dep = mkl_dep
else
  lapack_dep = dependency('lapack', required: false)
  blas_dep = dependency('blas', required: false)

  if not lapack_dep.found()
    lapack_lib = fc.find_library('lapack', required: true)
    lapack_dep = declare_dependency(dependencies: lapack_lib)
  endif

  if not blas_dep.found()
    blas_lib = fc.find_library('blas', required: true)
    blas_dep = declare_dependency(dependencies: blas_lib)
  endif
endif

# The openmp dependency is necessary for thermal_transport
openmp_dep = dependency('openmp', required: true)

# --- MPI Detection ---
# This overrides the logic in os.environ["MPICC"] and os.popen("%s -show" % mpicc).
# Meson has a built-in MPI module.
mpi_args = []
mpi_link_args = []
mpi_compile_args = []
has_mpi = false

# Attempts to find the MPI dependency.
# You can specify a specific MPI compiler with the 'mpi_compiler' parameter
# or, if you want, a specific Fortran compiler with 'mpi_fortran_compiler'.
# For OpenMPI, IntelMPI, MPICH, etc., Meson usually finds it automatically.
#mpi_dep = dependency('mpi', required: false, language: ['c', 'fortran'])
mpi_dep = dependency('mpi', required: false)

if mpi_dep.found()
  message('MPI environment detected correctly.')
  has_mpi = true
  # Meson handles adding appropriate flags. We just add the define.
  # If you need specific MPI flags beyond what Meson adds automatically,
  # you can get them via mpi_dep.get_compile_args() and mpi_dep.get_link_args()
  # and add them to extra_compile_args/extra_link_args.
  mpi_compile_args += ['-D_MPI']
else
  # Here you can add warning logic if MPI is not found.
  # Meson prints a warning if required: true and it is not found.
  # For required: false, you can print your own warning.
  warning('No MPI compiler found, please ensure MPI is installed and configured.')
  warning('If you wish to activate MPI acceleration, consider setting MPICC environment variable or providing Meson with appropriate flags.')
endif
# Find the quadmath library, if available
quadmath_dep = fc.find_library('quadmath', required: false)

# --- NUMPY CONFIGURATION ---
# Gets the path to the NumPy and f2py header directories using the Python command
incdir_numpy = run_command(py,
    ['-c', 'import numpy; print(numpy.get_include())'],
    check : true
).stdout().strip()

# f2py also requires the fortranobject.h header
incdir_f2py = run_command(py,
    ['-c', 'import numpy.f2py; print(numpy.f2py.get_include())'],
    check : true
).stdout().strip()

inc_np = include_directories(incdir_numpy, incdir_f2py)
np_dep = declare_dependency(include_directories: inc_np)

inc_f2py = include_directories(incdir_f2py)
fortranobject_c = incdir_f2py / 'fortranobject.c'

# --- END OF NUMPY CONFIGURATION ---
if openblas_dep.found()
  message('openblas environment detected correctly.')
  list_dep = [py_dep, mpi_dep, quadmath_dep, openblas_dep, lapack_dep, blas_dep]
else
  warning('No openblas found.')
  list_dep = [py_dep, mpi_dep, quadmath_dep, lapack_dep, blas_dep]
endif
# --- Definition of each Python extension (Fortran) ---

# 'symph' extension

# Compilation of the Fortran module: symph
fortran_sources_fforceslibs = [
    'src/get_forces_energies.f90',
    'src/v2_0_harmonic.f90',
    'src/lattice.f90',
    'src/get_harmonic_force.f90'
]
## Generate the C wrapper with f2py using a custom target
f2py_fforceslibs_target = custom_target('fforceslibs-f2py-wrapper',
    input: fortran_sources_fforceslibs,
    output: ['fforceslibsmodule.c','fforceslibs-f2pywrappers.f'],
#    command: [py.full_path(), '-m', 'numpy.f2py', '--backend', 'meson',
#        '--dep', 'mpi', '--quiet', '-c', '@INPUT0@', '-m', 'fforceslibs'],
     command : [py, '-m', 'numpy.f2py', '@INPUT@', '-m', 'fforceslibs', '--lower'],
    install: false
)
py.extension_module('fforceslibs',
   [
    fortran_sources_fforceslibs,
    f2py_fforceslibs_target, fortranobject_c],
    include_directories: inc_np,
    dependencies: list_dep,
#    link_args: ['-L' + py.get_install_dir() / 'numpy' / 'f2py' / 'src' / 'fortranobject.c', '-lfortranobject'],
    install: true
)


# --- Installation of the 'cellconstructor' Python package ---
#install_data(
#  'cellconstructor/__init__.py', 'cellconstructor/AnharmonicForceFields.py', 'cellconstructor/calculators.py',
#  'cellconstructor/Methods.py', 'cellconstructor/Phonons.py', 'cellconstructor/Spectral.py',
#  'cellconstructor/ThermalConductivity.py', 'cellconstructor/Units.py', 'cellconstructor/Bands.py',
#  'cellconstructor/ForceTensor.py', 'cellconstructor/Manipulate.py', 'cellconstructor/Moro_object.py',
#  'cellconstructor/Settings.py', 'cellconstructor/Structure.py', 'cellconstructor/symmetries.py',
#  'cellconstructor/Timer.py',
#  install_dir: py.get_install_dir() / 'cellconstructor',
#)
py.install_sources(
    [
        'Modules/Calculator.py',
        'Modules/__init__.py',
    ],
    subdir: 'fforces'
)
#
# Set the tests by pytest.
pytest_exe = find_program('pytest', required: false)

if pytest_exe.found()
  test('pytest', pytest_exe,
    args : ['-v'],
    workdir : meson.project_source_root()
  )
else
  message('pytest not found; pytest tests are skipped.')
endif
