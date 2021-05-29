"""
This is a simple submission script for jobs with the SLURM scheduler.

On top of creating the necessary submission scripts, the BatchBuddha class reads
in configuration files and command line arguments, which are broadcasted to your
run scripts. 
It automatically loops over the parameters you specified as
loopableConfigEntries in your cfg file and creates one job for each setting.

Should be used in conjunction with the Configaro module.

@author Eric "Dr. Dre" Drechsler (eric.drechsler@cern.ch)
"""

import sys,os,time
import logging
logging.basicConfig( level=logging.INFO, format='%(levelname)-8s %(name)s %(message)s' ) 
logger = logging.getLogger(__name__)

from submissionTemplates import SLURM_JOB_TEMPLATE, setup_cedar
from subprocess import Popen, PIPE, STDOUT
from configaro import Configaro
import helpers
import itertools
import gin

def generatePositiveHash(val):
    """
    Create a unique hash for a given string.
    """
    hashVal=hash(val)
    if hashVal<0:
        hashVal+=sys.maxsize+1
    return str(hashVal)

class BatchBuddha(object):
    """
    Main submission interface class.
    """
    def __init__(self, config=None):
        #requires a configuration (namespace)
        assert config is not None, "Config not defined"
        self.config=config
        
        #set cluster node options
        self.submissionTemplate=self.config.submissionTemplate
        self.baseOutputDir=helpers.getBaseOutputDir()
        self.logDir=os.path.join(self.baseOutputDir,self.config.logOutputFolder)
        helpers.mkdir_p(self.logDir) 
            
        #set job specific templates
        self.nodeSetupTemplate=setup_cedar
        self.submitScriptTemplate=SLURM_JOB_TEMPLATE
        self.runCommandTemplate=self.config.runCommand

        #create a dictionary from all the loopable parameters
        self.jobArguments=self._createConfigLoops()
        return

    #loops config namespace and creates dictionary
    #dict: argument : ["--argument a1", ...]
    def _createConfigLoops(self):
        """
            Main submission interface class.
        """
        logger.info("Creating argument dictionary by looping over config entries:\n{0}".format(self.config.loopableConfigEntries))
        argDict={}
        
        #loop config
        if isinstance(self.config.loopableConfigEntries, list):
            loopableEntries = self.config.loopableConfigEntries
        else:
            loopableEntries = self.config.loopableConfigEntries.split(",")
        for par in loopableEntries:
            try:
                # check if the loopableConfigEntry is defined in gin config
                val_list = gin.query_parameter(par)
                # it's a gin config
                if isinstance(val_list,list):
                    if not par in argDict: argDict[par]=[]
                    for val in val_list:
                        argDict[par].append((par, val))
            except ValueError:
                # seems to be in standard config
                for arg,val in self.config.allConfigKeys:
                    if par == arg:
                        # standard config
                        print("It's a normal config entry!")
                        # it's an entry in the standard config
                        if isinstance(val,list):
                            if not arg in argDict: argDict[arg]=[]
                            #add tuple to list - contains command line argument for batch job steering
                            for i in range(0,len(val)):
                                argDict[arg].append((arg,val[i]))
            
        logger.info("Created dictionary of job arguments:\n{0}".format(argDict))
        return argDict
        

    def setup(self):
        datetag=time.strftime("%y%m%d")

        #TODO make this 
        self.callDir=os.getcwd()
        
        self.jobList=[]
        #JOB LOOP
        #constructs unique ID and job setups for all iterable config entries
        batchCommands = []
        for jobConf in itertools.product(*self.jobArguments.values()):
            addArgList=[]
            idList=[]
            addGinArgList=[]
            for idxSet in range(0,len(jobConf)):
                if not len(jobConf[idxSet])==2:
                    logger.error("Something went wrong when unpacking job config.")
                    raise Exception()
                configArg=jobConf[idxSet][0]
                configVal=jobConf[idxSet][1]
                try:
                    gin.query_parameter(configArg)
                except ValueError:
                    addArgList.append("--{0} {1}".format(configArg,configVal))
                else:
                    addGinArgList.append("{0}={1}".format(configArg,configVal))
                idList.append(str(jobConf[idxSet][1]))

            if addGinArgList:
                addArgList.append("--ginBindings {}".format(" ".join(addGinArgList)))
            self.jobID = "_".join(idList) if len(idList) > 0 else "theOnlyJob"
            self.jobHash=generatePositiveHash(self.jobID)
            logger.info('Setting up job {1}: {0}'.format(self.jobHash,self.jobID))
            self.jobName='_'.join([datetag,self.jobID,self.jobHash])
            logger.info('JobName: {}'.format(self.jobName))
            
            self.runCommandArguments=" ".join(addArgList)
            logger.debug('Appending {0} to default run command'.format(self.runCommandArguments))
            self.runCommand=self.runCommandTemplate.format(
                jobOutputDir=os.path.join(self.config.outputFolderName, self.jobName)
            )
            #assembling runscript per node
            train=' '.join([self.runCommand.split("&&")[0]]+[self.runCommandArguments])
            # payload=' '.join([self.runCommand,self.runCommandArguments])
            payload = ' && '.join([train] + self.runCommand.split("&&")[1:])
            logger.info('Job: {0}'.format(payload))
            
            self.runScriptPath='{0}.sh'.format(self.jobName)
            self.runScriptPath=os.path.join(self.logDir,self.runScriptPath)
            runScript=open(self.runScriptPath, "w")

            # unique output dir
            self.outputDir=os.path.join(self.baseOutputDir, self.jobHash)
            
            nodeSetup=self.nodeSetupTemplate
            nodeSetup=nodeSetup.format()

            runScript.write("#!/bin/bash")
            runScript.write(nodeSetup)
            runScript.write(payload)
            # make run script executable
            os.chmod(self.runScriptPath, 509)
            runScript.close()

            #build submit script and log files
            self.submitScript="_".join([datetag,self.jobHash,"submit.sh"])
            self.submitScript=os.path.join(self.logDir,self.submitScript)
            self.logSubmit=self.submitScript.replace('.sh','.log')

            #create logfiles
            self.logExecute="_".join([datetag,self.jobHash,"run.log"])
            self.logExecute=os.path.join(self.logDir,self.logExecute)
            self.logError=self.logExecute
            
            logger.debug('Logfile for Execution: {0}'.format(self.logExecute))
            logger.debug('Submitfile: {0}'.format(self.submitScript))
            logger.debug('Logfile for Submission: {0}'.format(self.logSubmit))
               
            submitScript=open(self.submitScript, "w")
            submitScript.write(self.fillSubmitScriptTemplate(payload))
            submitScript.close()

            self.batchCommand=self.submissionTemplate.format(
                submitscript=self.submitScript
            )
            logger.info('batch command: {0}'.format(self.batchCommand))
            if not self.config.testRun:
                p = Popen(self.batchCommand, shell=True, stdout=PIPE, stdin=PIPE, stderr=PIPE)
                outs, errs = p.communicate()
                if errs:
                    logger.error('Could not submit jobs, the following error occured:')
                    logger.error(errs)
                    logger.info('The file \'submitJobs.sh\' will be created to execute the jobs later')
                    self.config.dumpSubmitCommandsToFile = True
            batchCommands.append(self.batchCommand)
        if self.config.dumpSubmitCommandsToFile:
            with open("submitJobs.sh", "w") as f:
                f.write("#!/bin/bash \n")
                f.write("module load python/3.6 \n")
                for c in batchCommands:
                    f.write(c+" \n")
                os.chmod("submitJobs.sh", 509)
            logger.info('Executable file \'submitJobs.sh\' has been created!')
        return

    #FIXME make use of this
    def launch(self):
        for job in self.jobList:
            logger.info("Submitting {0}: {1} ".format(job.jobHash,job.jobID))
            if not self.config.testRun:
                os.system(job.batchCommand)
    
    def fillSubmitScriptTemplate(self,payload):
        return self.submitScriptTemplate.format(
            project=self.config.project,
            logsdir=self.logDir,
            outdir=self.outputDir,
            local_scratch=self.config.local_scratch,
            time=self.config.time,
            cores=int(self.config.cores),
            memory=self.config.memory,
            jobname=self.jobName,
            payload=payload,
            runscript=self.runScriptPath
        )        

if __name__ == '__main__':
    
    c=Configaro()
    # gin.parse_config_file(c.dataPrepConfig)
    # gin.parse_config_file(c.trainingSpecsConfig)
    
    bb=BatchBuddha(config=c)
    bb.setup()
    
