% de - combines 2 images from double echo sequence for fMRI analysis
%
%      usage: [  ] = de( filename1, filename2, echoTimes, varargin )
%    contrib: sue franics, alex beckett + ds
%             original script by roman wesolowski
%        $Id: de.m 11 2010-06-03 11:01:48Z denis $:
%
%     inputs: filename1 - filename for echo1
%             filename2 = filename for echo2 
%                   [assumes 4D image files,.hdr/img, floating point recommended] 
%             echoTimes - in ms, e.g.[15 40]
%             
%  Several options can be set (using evalargs syntax):
%
%     - method: specify which of the echo comination procedures to use.
%              
%              1: T2* weighted, 
%              2: SNR weighted (not implemented yet)
%              3: simple summation (e1+e2)  
%              4: all of the above
%
%       de('echo1.img', 'echo2.img', [25 40], 'method=3')
%
%
%     - noiseCutoff:  cutoff level for noise in input data (intensity in echo 1), 
%                        values below this will be treated as zero during the 
%                        calculations
%
%       de('echo1.img', 'echo2.img', [25 40], 'noiseCutoff=75')        
%                  
%
%     - T2slimit: in order to deal with the overly large T2* limits that
%                 can be thrown out during T2* estimation and weighting method,
%                 specify an upper limit (in ms) to be the cutoff point. Values above this value will be set to 0:
%                           
%       de('echo1.img', 'echo2.img', [25 40], 'T2slimit=1000')
%          
%
%
%
%    outputs: 
%             filename_T2s_av.hdr/img - 3d file containing average T2s values
%             filename_T2s.hdr/img    - 4d file containing T2s values at each dynamic
%             filename_ss_map.hdr/img - 4d file containing SIMPLE summation images
%             filename_ws_map.hdr/img - 4d file containing WEIGHTED summation images
%
%
%    purpose: change sue and roman's code to be more generic and
%             mrTools compatible
%
%    see also: evalargs, multiEchoNew
%
%        e.g: de('e1.nii', 'e2.nii', [25 40])
%
function [  ]=de( fileName_e1, fileName_e2, echoTimes, varargin )

% ----------------------------------------------------------------------
% this function is based on a script 
% combining_2echos_spm_noloops_sue
% originally:
% READS IN 2-ECHO DATA AND COADDS WITH T2* WEIGHTING  
% BY ROMAN WESOLOWSKI AND SUE                        


% ----------------------------------------------------------------------
% parse input args
% ----------------------------------------------------------------------
% the following line sets input parameters that were passed after the filename1, %filename2 and echoTimes inputs. 
% See help for evalargs to see how this works:

validInputArgs = {'method', ... % which combination method (1=T2* weighed, 2=SNR weighted, 3=summation, 4=all
            'noiseCutoff', ... % zero input data below this intensity value first
            'T2slimit', ... % upper clipping range for T2* map if T2* weighting used, 1000 ms default
            };
 
eval(evalargs(varargin,[],[],validInputArgs));

% Name and path of outcoming and incoming files
if nargin == 1 || (nargin > 2 && ischar(echoTimes))
  % with the new input conventions, 0,2,3, many input args are allowed
  help de
  return
end

% decide which method to use if not defined
if ieNotDefined('method') || method > 4
    method = 4;
    if method > 4, fprintf ('Invalid option, will use all');end
    if isempty(method), method = 4;end
end

if method == 2
  display('(uhoh) you asked for SNR weighted combinaton only; this is not implemented yet!')
  disp('no files written!')
  return
end


% if filenames are not given correctly, get via UI
if ieNotDefined('fileName_e1') ||  ieNotDefined('fileName_e2') 
  % get filenames
  % if user presses cancel in either case, abort.
  [fileName_e1,pathName_e1] = uigetfile({'*.img';'*.hdr'},'Input File echo_1 (4D file)');
  if isequal(fileName_e1,0),  disp('User pressed cancel @ file 1'), return, end
  [fileName_e2,pathName_e2] = uigetfile({'*.img';'*.hdr'},'Input File echo_2 (4D file)');
  if isequal(fileName_e2,0),  disp('User pressed cancel @ file 2'), return, end
end

% check if echo times are passed in.
% the numel~=2 check catches the case when user starts entering 'options=value' after filenames
if ieNotDefined('echoTimes') || numel(echoTimes) ~= 2
  TE1=input('First echo time [ms]: ');
  TE2=input('Second echo time [ms]: ');
else
  TE1 = echoTimes(1);
  TE2 = echoTimes(2);
end
fprintf('Using echo times: %.2f, %.2f\n', TE1, TE2)

% check that echo times are reasonable
if TE1 > TE2
  disp('(uhoh) te1 is larger than te2 - that doesn''t make sense. Check your inputs.')
  return
end
    
% collects filename stem for saving unique output files
pat = 'echo\d\d';
[a,str,ext] =  fileparts(fileName_e1);
match = regexp(str, pat, 'match'); 
filestem = stripext(str,match{1});
if strcmp(ext, '.nii')
  hdr=ext; img=ext;
else
  hdr='.hdr'; img='.img';
end

% save output images here - will just save images in same folder as originals.
if ieNotDefined('pathName_e1'), pathName_e1 = './'; end
pathName_out = pathName_e1;

%% Read in selective images
% Open the raw data for analysis - echo_1
disp('Opening file - echo1');
try
    [tc4d_e1, hdr_e1]=cbiReadNifti([pathName_e1,fileName_e1]);
catch
    disp('Error loading Echo 1, please ensure that the input file does not have any missing volumes, corrupted hdr, etc...'),return
end
% Open the raw data for analysis - echo_2
disp('Opening file - echo2');
try
    [tc4d_e2, hdr_e2]=cbiReadNifti([pathName_e1,fileName_e2]);
catch
    disp('Error loading Echo 2, please ensure that the input file does not have any missing volumes, corrupted hdr, etc...'),return    
end
% checks that images are the same size
if size(tc4d_e1) ~= size(tc4d_e2)
  disp('[warning] sizes of echo1 and echo2 data don''t mix ');
end

% the following lines are necessary to fix qform errors that lead to erroneous pixels sizes when saving outputs 
% - add option to fix hdr's in original files?
hdr_e1.qform44 = [ diag(hdr_e1.pixdim(2:4)), zeros(3,1);  0 0 0 1]; 
disp('Resetting Qform to match voxel dimensions to correct errors arising from ptoa');
disp('Qform44'),disp(hdr_e1.qform44)

if hdr_e1.qform_code == 0
      disp('(uhoh) qform_code==0, resetting to 1')
      hdr_e1.qform_code = 1;
end

% there are lots of divide by zeros here: switch warning off for this calculation:
w_ = warning('off', 'MATLAB:divideByZero');
w_ = warning('off', 'MATLAB:log:logOfZero');

% if the previous size check went ok, then images have same dimensions
% take the dims of the first on in x,y,z,t
xdim=size(tc4d_e1,1); 
ydim=size(tc4d_e1,2); 
zdim=size(tc4d_e1,3); 
tvols=size(tc4d_e1,4);

% T2* weighting or "ALL"
if method==1 || method==4
    
    % get noise level if not passed
    if ieNotDefined('noiseCutoff') || numel(noiseCutoff) >1
      noiseCutoff = input('Input estimate for noise level for use in T2* calculation\n (manually examine area of 2nd echo image outside the head in to estimate value - 10000 recommended for general use): ');
    end
    if isempty(noiseCutoff), noiseCutoff=0;end
    fprintf('Using noise cutoff level %.2f\n', noiseCutoff)
    
    % set T2* limit if not specified earlier
    if ieNotDefined('T2slimit'), T2slimit = 1000;end
    fprintf('Using upper T2* limit of %d ms\n', T2slimit);
    
    disp('Combining echoes...');
    tc4d_e1_av=mean(tc4d_e1,4);
    tc4d_e2_av=mean(tc4d_e2,4);

    % preallocate memory; make space for T2s_av
    T2s_av = nan(size(tc4d_e2_av));
    % make a noise mask - then only calculate where the noise is exceeded...
    dataIdx = (tc4d_e1_av>noiseCutoff);
    % do the actual calculation
    T2s_av(dataIdx) = (TE2-TE1)./(log(tc4d_e1_av(dataIdx))-log(tc4d_e2_av(dataIdx)));

    % Deal with disallowed T2* values...
    badIdx = ( isnan(T2s_av) | isinf(T2s_av) | T2s_av < 0 | T2s_av > T2slimit );
    T2s_av(badIdx) = NaN; % make nan instead of 0 (because we normalize by this number later)
    
    % Save combined image
    
    % preallocate space for the combined 4D image
    tc4d = zeros(xdim, ydim, zdim, tvols);
    
    % Calcuate T2* weighted combination
    fprintf('Doing weighted combination for echo 1...')
    for iDyn = 1:tvols;
      tc4d(:,:,:,iDyn)=tc4d_e1(:,:,:,iDyn).*(TE1./T2s_av)...
          .*exp(-TE1./T2s_av)+tc4d_e2(:,:,:,iDyn).*(TE2./T2s_av).*exp(-TE2./T2s_av);
      if (rem(iDyn/tvols,.05)==0)
            fprintf('%i%%...',100*(iDyn/tvols))
      end
    end
    fprintf('Completed!\n')
    
    % clean up NAN and INF voxels... make structural zeros
    badIdx = ( isnan(tc4d) | isinf(tc4d));
    tc4d(badIdx) = 0;
    
    % Save combined image file with timing and transform info from Echo 1 Header
    com_hdr = hdr_e1;
    com_hdr.hdr_name = [filestem,'ws_map',hdr];
    com_hdr.img_name = [filestem,'ws_map',img];
    com_hdr.descrip = ['Combined Echoes from', filestem];
    fileName_out = [pathName_out,filestem,'ws_map',img];
    fprintf('Saving 4d t2* weighed file: %s\n', fileName_out);
    cbiWriteNifti(fileName_out,tc4d,com_hdr);
    
    % clean up NAN voxels in T2s_av image... make structural zeros
    badIdx = ( isnan(T2s_av));
    T2s_av(badIdx) = 0;

    % Save T2s_av - the fitted average T2s values.
    T2s_av_outfilename = [pathName_out,filestem, 'T2s_av',img];
    T2s_av_hdr = hdr_e1;
    T2s_av_hdr.hdr_name = [filestem,'T2s_av',hdr];
    T2s_av_hdr.img_name = [filestem,'T2s_av',img];
    T2s_av_hdr.descrip = 'Fitted average T2*';
    T2s_av_hdr.dim(5) = 1; % time
    T2s_av_hdr.pixdim(4) = 1; % time
    fprintf('Saving T2* average (in ms) data: %s\n', T2s_av_outfilename);
    cbiWriteNifti(T2s_av_outfilename,T2s_av,T2s_av_hdr);
    
    %preallocate space for 4D T2* image
    T2s = zeros(xdim, ydim, zdim, tvols);
    
    % Calculate the fitted 4D% T2s values.
    fprintf('Calculating 4D T2* image...')
    for iDyn =1:tvols     
        T2s(:,:,:,iDyn)=(TE2-TE1)./(log(tc4d_e1(:,:,:,iDyn).*(tc4d_e1(:,:,:,iDyn)>noiseCutoff))-log(tc4d_e2(:,:,:,iDyn).*(tc4d_e2(:,:,:,iDyn)>noiseCutoff)));
        if (rem(iDyn/tvols,.05)==0)
            fprintf('%i%%...',100*(iDyn/tvols))
        end
    end
    fprintf('Completed!\n')
    
    % anything that goes outside of the limits is set to 0:
    badIdx = ( isnan(T2s) | isinf(T2s) | T2s < 0 | T2s > T2slimit); 
    T2s(badIdx) = 0;

    % Save out 4D T2* file
     
    T2s_outfilename = [pathName_out,filestem, 'T2s',img];
    T2s_out_hdr = hdr_e1;
    T2s_out_hdr.hdr_name = [filestem,'T2s',hdr];
    T2s_out_hdr.img_name = [filestem,'T2s',img];
    T2s_out_hdr.descrip = 'Fitted 4d T2*';
    fprintf('Saving 4d T2* (in ms) data: %s\n', T2s_outfilename);
    cbiWriteNifti(T2s_outfilename,T2s, T2s_out_hdr);
    
   
end

%% SNR combination

if (method == 2) || (method == 4)
   disp('awaiting maths for SNR combination') 
end

%% Simple Summation

if (method == 3) || (method == 4) 
  tc4d_ss = tc4d_e1+tc4d_e2;
  ss_hdr = hdr_e1;
  ss_hdr.hdr_name = [filestem,'ss_map',hdr];
  ss_hdr.img_name = [filestem,'ss_map',img];
  ss_hdr.descrip = ['Combined Echoes from', filestem];
  fileName_out = [pathName_out,filestem,'ss_map',img];
  fprintf('Saving 4d summated file: %s\n', fileName_out);
  cbiWriteNifti(fileName_out,tc4d_ss,ss_hdr);
end

% switch divide by zero warning on again:
w_ = warning('on', 'MATLAB:divideByZero'); 
w_ = warning('on', 'MATLAB:log:logOfZero');

disp('(de) Done!')

return













