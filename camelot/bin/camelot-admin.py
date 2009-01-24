
def main():
  from optparse import OptionParser
  parser = OptionParser(usage='usage: %prog [options] startproject project')
  (options, args) = parser.parse_args()
  command, project = args
  import shutil, os
  shutil.copytree(os.path.join(os.path.dirname(__file__), '..', 'empty_project'), project)
  
  
if __name__ == '__main__':
  main()