% mr_isfile.m
%
%      usage: mr_isfile(filename)
%         by: justin gardner
%       date: 08/20/03
%       e.g.: mr_isfile('filename')
%    purpose: function to check whether file exists
%
% OLD: function [isit permission] = isfile(filename)
function [isit, permission] = mr_isfile(filename)

isit = 0;
permission = [];
if (nargin ~= 1)
  help mr_isfile;
  return
end

% open file
fid = fopen(filename,'r');

% check to see if there was an error
if (fid ~= -1)
  fclose(fid);
  [dummy, permission] = fileattrib(filename); %#ok<ASGLU>
  isit = 1;
else
  isit = 0;
end
