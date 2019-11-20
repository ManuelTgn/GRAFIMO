"""

@author: Manuel Tognon

@email: manu.tognon@gmail.com
@email: manuel.tognon@studenti.univr.it


The script defines the pipeline for the creation and indexing of the 
graph genome, needed for the following steps.


"""

import subprocess
import os
import glob
from grafimo.utils import CHROMS_LIST, die
from grafimo.GRAFIMOException import VGException, ValueException

def get_genome_from_ucsc():
    """
        Returns the reference genome hg38 from ucsc
        ----
        Parameters:
            None
        ----
        Returns:
            genome (str) : path to the genome downloaded (in .fa format)
    
    """
    
    cmd='wget -c ftp://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/hg38.fa.gz'
    code=subprocess.call(cmd, shell=True)
    
    if code!=0:
        raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
        die(1)
        
    else:
        genome_comp='./hg38.fa.gz'
        genome='./hg38.fa'
        
        cmd='gunzip {0}'.format(genome_comp)
        code=subprocess.call(cmd, shell=True)

        if code != 0:
            raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
            die(1)

        cmd='rm {0}'.format(genome_comp)
        code=subprocess.call(cmd, shell=True)

        if code != 0:
            raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
            die(1)
            
        else:
            return genome
        
    return os.getcwd() # if something goes wrong we return the cwd
        
def get_1000GProject_vcf():
    """
        Returns the vcf file from the 1000 Genome Project
        ----
        Parameters:
            None
        ----
        Returns:
            vcf (str) : path to the vcf downloaded vcf file (in .vcf.gz)
    """
    
    cmd='http://ftp.1000genomes.ebi.ac.uk/vol1/ftp/data_collections/'
    cmd+='1000_genomes_project/release/20190312_biallelic_SNV_and_INDEL/'
    cmd+='ALL.wgs.shapeit2_integrated_snvindels_v2a.GRCh38.27022019.sites.vcf.gz'
    
    code=subprocess.call(cmd, shell=True)
    
    if code!=0:
        raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
        die(1)
        
    else:
        vcf='./ALL.wgs.shapeit2_integrated_snvindels_v2a.GRCh38.27022019.sites.vcf.gz'
        return vcf
            
        
def create_vg(chroms, linear_genome='', vcf=''):
    """
        Creates the graph genome, given in input a linear reference and a vcf file.
        They are created chromosome by chromosome.
        ----
        Parameters:
            chroms (list) : list of chromosomes for which the genome graph will be
                            created; if empty all chromosomes will be taken into
                            account
            linear_genome (str) : path to the linear genome
            vcf (str) : path to the vcf file
        ----
        Returns:
            fileloc (str) : path to the location of the graph genomes        
    """
    
    if not linear_genome:
        # get it from UCSC
        linear_genome=get_genome_from_ucsc()
    elif linear_genome:
        NO_LINEAR_GENOME_INPUT=False
        
    if not vcf:
        # get it from 1000 genome project
        vcf = get_1000GProject_vcf()
    elif vcf:
        NO_VCF_INPUT=False
        
    if not chroms:
        chroms=CHROMS_LIST
        
    cwd=os.getcwd()
    
    if not tbiexist(cwd):
        msg=''.join([vcf, ".tbi file not found indexing with tabix..."])
        print(msg)
        cmd='tabix -p vcf {0}'.format(vcf) #
        code=subprocess.call(cmd, shell=True)

        if code!=0:
            raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
            die(1)
    
    if linear_genome[0:6]=='/Users':
        pass
    else:
        linear_genome=''.join(['./', linear_genome])
        
    if vcf[0:6]=='/Users':
        pass
    else:
        vcf=''.join(['./', vcf])
    
    for chrom_n in chroms:
        chrom=''.join(['chr', chrom_n])
            
        vg=chrom+'.vg'
        xg=chrom+'.xg'
        
        vg_construct='vg construct -C -R {0} -p -n {1}={2} -r {3} -v {4} > {5}'.format(chrom_n, chrom_n, \
                                                                                     chrom, linear_genome, vcf, vg)
        
        code=subprocess.call(vg_construct, shell=True)

        if code!=0:
            msg='error in vg construct. '
            msg+='Unable to build the vg of the genome using {0} and {1}'.format(linear_genome,
                                                                                    vcf)
            raise VGException(msg)
            
        print('Indexing the VG...')
            
        vg_index='vg index -p -x {0} {1}'.format(xg, vg)
        code=subprocess.call(vg_index, shell=True)

        if code != 0:
            msg = 'error in vg index. '
            msg += 'Unable to build the vg of the genome using {0} and {1}'.format(linear_genome,
                                                                               vcf)
            raise VGException(msg)

        cmd='rm {0}'.format(vg)
        subprocess.call(cmd, shell=True)
        
        if code!=0:     # we have errors in the vg indexing
            raise SubprocessException(' '.join(["An error occurred while executing", cmd, ". Exiting"]))
            die(1)
            
    fileloc=os.getcwd()
    
    return fileloc

def indexVG(vg):
    """
        Index the vg genome graph [vg => xg] and returns the path to it
        ----
        Parameters:
            vg (str) : path to the vg genome graph
        ----
        Returns:
            fileloc (str) : path to the indexed genome graph (xg)
    """
    
    if not isinstance(vg, str):
        raise ValueException("Not valid path to the genome graph. Cannot proceed")
        
    else:
        xg=vg.split('.')[-2] # please avoid paths that contains '.' in the middle
        xg+='.xg'
        vg_index='vg index -p -x {0} {1}'.format(xg, vg) 
        code=subprocess.call(vg_index, shell=True)
        
        if code!=0:
            raise VGException('Error in vg index. Unable to index the geneome graph')
            die(1)
        
        # the xg is saved in the vg directory
        fileloc=os.getcwd()
        
        return fileloc 


def tbiexist(directory):
    """
        Check if there are vcf files that have been processed with tbi
        ----
        Parameters:
            directory (str) : directory where files will be checked
        ----
        Returns:
            (bool) 
    """

    path=''.join([directory, '/*.tbi'])
    tbi=glob.glob(path)

    if len(tbi) > 0:
        return True
    
    return False
        