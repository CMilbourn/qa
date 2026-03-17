function fixQformDE

[filename,pathname] = uigetfile({'*.img';'*.hdr''*.nii'},'Select the file(s) to convert','MultiSelect','on');

if ~iscell(filename)
   filename = {filename};
end

for i_file = 1:length(filename)

[a,b]=cbiReadNifti([pathname filename{i_file}]);
b.qform44 = [ diag(b.pixdim(2:4)), zeros(3,1);  0 0 0 1];
if b.qform_code == 0
      disp('(uhoh) qform_code==0, resetting to 1')
  b.qform_code = 1;
end

cbiWriteNifti([pathname filename{i_file}],a,b);

end