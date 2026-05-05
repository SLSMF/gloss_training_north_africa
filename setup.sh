conda init -q 
conda deactivate
conda env remove -n 'selene_training' -yq

conda env create -n selene_training -f selene_training.yml -yq
conda init -q
#conda activate selene_training 
#conda install ipykernel -yq
#python -m ipykernel install --user --name=selene_training --display-name "Python(selene_training)"