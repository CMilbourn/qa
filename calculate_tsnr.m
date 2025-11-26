function tsnr_map = calculate_tsnr(fMRI_data_4D)
% calculate_tsnr Computes the tSNR map from 4D fMRI data
% fMRI_data_4D is a 4D matrix (voxels_x, voxels_y, voxels_z, time_points)

% Calculate the mean signal across the time dimension (4th dimension)
mean_image = mean(fMRI_data_4D, 4);

% Calculate the standard deviation across the time dimension
std_image = std(fMRI_data_4D, 0, 4);

% Compute tSNR: mean / standard deviation
% Be careful with division by zero or near-zero values outside the brain mask.
tsnr_map = mean_image ./ std_image;

% Optional: Mask the tSNR image to include only brain voxels 
% to avoid artificially high tSNR values in the background noise
% (where both mean and std dev are very low).

end