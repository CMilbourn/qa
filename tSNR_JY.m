% --- MATLAB code to load NIfTI, calculate tSNR, and SAVE as NIfTI ---
% 20251124 JeYoung Jung
% edits by Colette Milbourn 
% 1. Load the NIfTI data
nii_filename = 'swrTASK_fMRI_TR2000.nii';

% Initialize original_nii_info to make sure it's available for spatial info extraction
original_nii_info = []; % For niftiinfo if we were to use it (but we'll skip for saving)
V_spm = []; % Initialize SPM volume info

% Method: Using SPM (requires SPM toolbox to be set up) - Most robust for this task
try
    V_spm = spm_vol(nii_filename); % Get SPM volume info (array of structs, one for each volume)
    fMRI_data_4D = spm_read_vols(V_spm); % Read data
    disp('NIfTI data loaded successfully using SPM.');
catch SPM_ME
    disp(['Could not load with SPM: ' SPM_ME.message]);
    error('Failed to load NIfTI data. Please ensure SPM is installed and configured in your MATLAB path.');
end

% Ensure the data is in double precision for calculations if it's not already
fMRI_data_4D = double(fMRI_data_4D);

% 2. Calculate the tSNR using your function
tsnr_map = calculate_tsnr(fMRI_data_4D);

% Optional: Handle NaN/Inf values (e.g., set to 0 or a very small number)
tsnr_map(isnan(tsnr_map)) = 0;
tsnr_map(isinf(tsnr_map)) = 0;


% 3. Save the tSNR map as a .nii file using SPM functions (Method B)

output_tsnr_filename = 'tsnr_map_swrTASK_fMRI.nii';

disp('Saving tSNR map using SPM functions...');

% Create a new header structure based on the original's first volume
% This copies all the necessary spatial transformations (origin, voxel size, orientation)
V_out = V_spm(1); % Start with a copy of the first volume's header (as a template)

% Update relevant fields for the new 3D tSNR map
V_out.fname = output_tsnr_filename; % New output filename
V_out.dim   = size(tsnr_map);       % New dimensions (will be 3D: [x, y, z])
V_out.dt    = [spm_type('float32') spm_platform('bigend')]; % Output as float32, ensures matches SPM's endianness
V_out.pinfo = [1;0;0]; % Scaling info: [slope; intercept; unused]. Set to 1,0,0 for raw values
V_out.descrip = 'Temporal SNR map calculated from fMRI data'; % Custom description

% If you want to explicitly clear time-related fields if they exist in pinfo
if numel(V_out.pinfo) > 3
    V_out.pinfo(4:end) = 0;
end

% Create and write the volume
% spm_create_vol initializes the NIfTI file on disk with the header
% spm_write_vol writes the actual 3D data into that file
V_out = spm_create_vol(V_out);
spm_write_vol(V_out, tsnr_map);

disp(['tSNR map saved as: ', output_tsnr_filename]);


% --- Visualization Example (for a middle slice) ---
figure;
middle_z_slice = round(size(tsnr_map, 3) / 2);
imagesc(tsnr_map(:,:,middle_z_slice));
colorbar;
axis image;
title(sprintf('tSNR Map (Axial Slice %d) for %s', middle_z_slice, nii_filename));
xlabel('X voxels');
ylabel('Y voxels');
colormap('jet'); % Good for visualizing gradients