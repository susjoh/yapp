import logging
from collections import defaultdict
import numpy as np
from scipy.stats import binom
from . import vcf, gamete, pedigree, family_phaser, MALE, FEMALE

logger = logging.getLogger(__name__)

def post_G( x, d):
    nh = len(x)
    lik00 = binom.pmf( x, d, p=0.5*f)*p00
    lik01 = binom.pmf( x, d, p=0.5*(f+0.5))*p01
    lik11 = binom.pmf( x, d, p=0.5*(f+1))*p11
    sump = lik00 + lik01 + lik11
    return np.array([ x/sump for x in [lik00, lik01, lik11]])

def genotype_from_gametes(gametes, pgeno=0.95, gerr=1e-2):
    '''Infer genotype from an array of gametes

    Parameters
    ----------
    gametes : numpy array of int
       The haplotypes of gametes. Rows are gametes, columns are SNPs. 0 = REF, 1 = ALT, -1 = Missing
    pgeno : float
       Minimum probability to call a genotype

    gerr : float
       Genotyping error rate

    Returns
    -------
    numpy array of int
        genotype of the parent 0 = REF/REF, 1 =REF/ALT, 2 = ALT/ALT, -1 = Missing
    
    '''
    nchrobs = np.sum(gametes>-1, axis=0)
    nalt = np.sum(gametes==1, axis=0)
    lik = np.zeros( (3, nalt.shape[0]), dtype=np.float)
    lik[0,] = binom.pmf( nalt, nchrobs, gerr)
    lik[1,] = binom.pmf( nalt, nchrobs, 0.5)
    lik[2,] = binom.pmf( nalt, nchrobs, 1-gerr)
    lik /= np.sum(lik, axis=0, keepdims=True)
    bestg = np.argmax(lik, axis=0)
    bestp = np.max(lik, axis=0)
    genotype = np.where(bestp>pgeno, bestg, -1)
    return genotype

def recmap( phys_pos, recrate=1):
    distances=np.array(phys_pos[1:] - phys_pos[:-1])
    distances[distances<100]=100
    return distances*recrate*1e-8

def main(args):
    prfx=args.prfx
    vcf_file = f"{prfx}.vcf.gz"
    fam_file = f"{prfx}.fam"

    ped = pedigree.Pedigree.from_fam_file(fam_file, parent_from_FID=True, default_parent=FEMALE)
    for fam in ped.families:
        assert len(fam.founders)==1
        trgt_i = fam.founders[0].indiv
        oprfx=f"{prfx}_{trgt_i}"
        logger.debug(f"{trgt_i} with {len(fam.non_founders)} gametes")
        logger.info(f"Getting gamete data for individual {trgt_i}")
        gam_data=vcf.vcf2zarr(vcf_file, output_prefix=oprfx,samples=[x.indiv for x in fam.non_founders], mode='inbred',maf=0)
        gam_data.create_group("parent")
        logger.debug(f"\n {gam_data.tree()}")
        for reg in gam_data['regions']:
            gam_hap = np.array(gam_data[f'genotypes/{reg}'])
            g = genotype_from_gametes(gam_hap, pgeno=args.pgeno, gerr=args.err)
            chrom_pair = family_phaser.ChromosomePair(g)
            children_gametes = dict(zip(gam_data['samples'], [ gamete.Gamete(h) for h in gam_hap]))
            
            logger.info('\tPhase from genotypes')
            wcsp_gam =  gamete.Gamete.from_wcsp_solver(g, children_gametes)
            logger.debug(f"\n {gam_hap[:, :10]}")
            logger.debug(f"{g[:10]}")
            logger.debug('-'*10)
            logger.debug(f"WCSP: {wcsp_gam.haplotype[:10]}")
            chrom_pair.update_unknown_gamete(wcsp_gam)
            logger.debug(f'h.pat: {chrom_pair.paternal_gamete.haplotype[:10]}')
            logger.debug(f'h.mat: {chrom_pair.maternal_gamete.haplotype[:10]}')
            
            logger.info('\tPhase from segregations')
            reg_map = recmap(np.array(gam_data[f"variants/{reg}/POS"]))
            inconsistencies=[ defaultdict(int), defaultdict(int) ]
            for sperm in children_gametes.values():
                si_sperm = chrom_pair.get_segregation_indicators( sperm , recmap=reg_map)
                ## impute paternal and maternal gametes at missing genotypes
                new_gametes = [ gamete.Gamete(chrom_pair.paternal_gamete.haplotype), gamete.Gamete(chrom_pair.maternal_gamete.haplotype)]
                for i,geno in enumerate(g):
                    if si_sperm[i][1]>0.999:
                        origin = si_sperm[i][0]
                        if geno==-1:
                            if new_gametes[origin].haplotype[i]<0:
                                new_gametes[origin].haplotype[i]=sperm.haplotype[i]
                            elif new_gametes[origin].haplotype[i]!=sperm.haplotype[i]:
                                inconsistencies[origin][i]+=1
            for locus in inconsistencies[0]:
                new_gametes[0].haplotype[locus]=-1
            for locus in inconsistencies[1]:
                new_gametes[1].haplotype[locus]=-1
            chrom_pair.update_paternal_gamete(new_gametes[0])
            chrom_pair.update_maternal_gamete(new_gametes[1])
                            
            logger.debug(f'h.pat: {chrom_pair.paternal_gamete.haplotype[:10]}')
            logger.debug(f'h.mat: {chrom_pair.maternal_gamete.haplotype[:10]}')
            ##
            ## save results
            ph_par = gam_data["parent"].create_group(reg)
            gametes = np.full( (2,gam_data["variants"][reg]['POS'].shape[0]), dtype='int8', fill_value=-2)
            gametes[0] = chrom_pair.paternal_gamete.haplotype
            gametes[1] = chrom_pair.maternal_gamete.haplotype
            ph_par['gametes']=gametes
                
    return

