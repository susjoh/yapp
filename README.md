# yapp : Yet Another Phasing Program

yapp is a program that includes a set of utilities to work on high
density genetic data in pedigrees. It is similar to other existing
softwares such as LINKPHASE, FIMPUTE, AlphaPhase ... . I
developed it for my own research to have a tool that is opensource and
that I can tweak to my own needs. 

If you find it useful for you, drop me a note on twitter
@BertrandServin. If you want to contribute ideas or code, you are
welcome if you know python :) 

yapp and its utilities implement some models and methods that have been
invented by other people. If you use yapp it is important that you
acknowledge their work by citing the appropriate
references. These will depend on the way you use the software. The
documentation below provides the relevant citations.

## Installation

The code includes a `setup.py` script that should take care of
installing yapp and *most* its dependencies. However some of them are
optional and must be installed if needed:

- ray : ray is an open source frame for building distributed
  applications. It is really only needed in yapp for parallelizing
  tasks on a computer cluster. If you don't plan to do that, or are
  satisfied using the multiprocessing approach you don't need to
  install it.
  
- numberjack : a python platform for combinatorial optimization. it is
  a python module so can be installed via pip. However the current
  setup script is buggy and installation must be tweaked. TODO: write
  instructions for installing numberjack properly with python 3.8.
  
I will upload a proper package on pypi when I have finished
implementing my initial ideas on the software.

## Usage

`yapp` has a command line interface that is used to launch different
commands. The basic syntax is :

```bash
yapp <command> <args1, args2, ..., argsN>
```
Most commands take has input files a [VCF file](http://samtools.github.io/hts-specs/VCFv4.2.pdf), its
index obtained with [`tabix`](http://www.htslib.org/doc/tabix.html), and a [FAM
file](https://www.cog-genomics.org/plink/1.9/formats#fam) with family
information. `yapp` writes logs of all commands to a common log file ending in `_yapp.log`. 
This way all steps of an analysis will be logged in the same place (the file is not overwritten).

Available commands are:

### `mendel`

This command performs checks for Mendelian errors between all parent -> offspring pairs. 
It will identify pairs that exhibit a large number of such errors and are therefore 
likely to be pedigree errors. It produces a new FAM file where such errors have been
removed and that can be used in subsequent analyses.

### `phase`

The `phase` command is used to infer gametic phase and segregation
indicators in a genotyped pedigree. The usage is:

```bash
yapp phase <prfx>
```

where `prfx` is the prefix of **all** input files :
`<path/to/prefix>.fam` , `<path/to/prefix>.vcf.gz` ,
`<path/to/prefix>vcf.gz.tbi`. Note that when exporting a `plink` bed
file to VCF, you must do so using `--recode vcf-iid` so that sample
names in the resulting VCF do no include the family-ID.

The events are logged in `<path/to/prefix>_yapp_phase.log`. The output
files produced are a phased VCF `<path/to/prefix>_phased.vcf.gz` and a
binary file `<path/to/prefix>_yapp.db`. This binary file is useful
for conducting analyses with other `yapp` commands.

#### Citation
`yapp phase` uses a Weighted Constraints Satisfaction Problem solver,
[https://miat.inrae.fr/toulbar2/](ToulBar2), to infer parental phase
from transmitted gametes. This idea was developped by Aurélie Favier
during her PhD with Simon de Givry and Andres Legarra.

<!-- [Favier, Aurélie (2011). Décompositions fonctionnelles et -->
<!-- structurelles dans les modèles graphiques probabilistes appliquées à -->
<!-- la reconstruction d'haplotypes.](http://thesesups.ups-tlse.fr/1527/) -->

[A. Favier, J-M. Elsen, S. de Givry, and A. Legarra
Optimal haplotype reconstruction in half-sib families
In ICLP-10 workshop on Constraint Based Methods for Bioinformatics,
Edinburgh, UK, 2010 ](https://miat.inrae.fr/degivry/Favier10a.pdf)

### `recomb`

## Other Utilities

### `fphtrain`

`fphtrain` trains a fastphase model on a set of individuals. It takes
as input a vcf_file (gzipped and indexed) and a number of haplotype
clusters. Genotype data can be read assuming different modes:

- genotype : unphased diploids
- phased : phased diploids. The phase information is taken from the
  VCF file (| sign). Unphased genotype are treated as missing.
- inbred : completely homozygous genotypes, treated as
  haploids. Heterozygote genotypes are treated as missing.
- likelihood : used the GL field from the VCF corresponding to the
  likelihood of each genotype on a PHRED scale (-10*log10(lik)).
  
#### Citation

[Scheet P, Stephens M. A fast and flexible statistical model for
large-scale population genotype data: applications to inferring
missing genotypes and haplotypic phase. Am J Hum
Genet. 2006;78(4):629-644. doi:10.1086/502802](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1424677/)

If you use the likelihood mode, cite:

[Linkage Disequilibrium-Based Quality Control for Large-Scale Genetic
Studies Scheet P, Stephens M (2008)](https://doi.org/10.1371/journal.pgen.1000147)
