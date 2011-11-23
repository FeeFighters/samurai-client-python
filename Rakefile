desc "Delete created files and directories."
task :clean do
  rm_rf "build"
  rm_rf "dist"
  rm_f "MANIFEST"
end

desc "Run tests."
task :test do
  sh "nosetests -v"
end

desc "Run tests on CI server."
task :test_ci do
  sh "nosetests -v --with-xunit --xunit-file=results.xml"
end

namespace :pypi do
  desc "Register the package with PyPI"
  task :register => :clean do
    sh "python setup.py register"
  end

  desc "Upload a new version to PyPI"
  task :upload => :clean do
    sh "python setup.py sdist upload"
    Rake::Task["clean"].reenable
    Rake::Task["clean"].invoke
  end
end

namespace :docs do
  desc "Generate html documentation"
  task :html do
    sh "PYTHONPATH='..' make -C docs clean html"
  end
end
