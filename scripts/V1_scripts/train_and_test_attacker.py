import numpy as np
import scipy.stats as stats
import scipy.signal as signal
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import time
import sys
import warnings
import scalogram
from sklearn import metrics
from sklearn import svm
from sklearn.cluster import DBSCAN
from sklearn.neural_network import MLPClassifier
warnings.filterwarnings('ignore')

# Debug mode
DEBUG = True

# Observation window
observationWindow = 540

# Perform K-fold validation (K = 5)
numberIterations = 5

# Wavelet scales
scales = [] #32, 64, 128

# Randomize windows
random = True

# Silence threshold
silence_threshold = 0

# Use sliding windows
sliding_windows = True

# Size of sliding window
sliding_window_size = 30


def getFullSampleSet(data, random=True, oWnd=540, sliding=True, stepsize=180):
	# Number of samples and number of columns
	nSamp,nCols=data.shape

	# Number of samples taken (nlines/obsWindow)
	nObs=int(nSamp/oWnd)

	# Sliding windows
	if sliding:

		# Create new array
		data_sli = np.vstack( data[i*stepsize:oWnd+i*stepsize] for i in range(0,nSamp) )

		# Number of samples and number of columns ()
		nSamp,nCols=data_sli.shape

		# Number of samples taken (nlines/obsWindow)
		nObs=int(nSamp/oWnd)

		# Delete last window if it is not completed
		data = data_sli

	# Delete last window if it is not completed
	data = data[:nObs*oWnd]

	# Reshape the data
	# Divide big array in sampling intervals
	data_obs=data.reshape((nObs,oWnd,nCols))

	if random:
		# Randomize data
		new_data = np.random.shuffle(data)
	
	return data_obs

def divideTrainingAndTestingSets(data, testIndex=0, testPerc=0.2):

	begTestSet = int(len(data)*testPerc*testIndex)
	endTestSet = int(len(data)*testPerc*(testIndex+1))

	trainSet1 = data[:begTestSet, :, :]
	trainSet2 = data[endTestSet:, :, :]

	return (data[begTestSet:endTestSet, :, :], np.vstack((trainSet1, trainSet2)))

def extractFeatures(data,Class=0):
	features=[]
	nObs,nSamp,nCols=data.shape

	# Create a vector filled with the class number
	oClass=np.ones((nObs,1))*Class
	for i in range(nObs):
		# Calculate maximum
		Max1=np.amax(data[i,:,:],axis=0)

		# Calculate minimum
		Min1=np.amin(data[i,:,:],axis=0)
		
		# Calculate mean
		M1=np.mean(data[i,:,:],axis=0)
		
		# Calculate median
		Md1=np.median(data[i,:,:],axis=0)

		# Calculate standard deviation
		Std1=np.std(data[i,:,:],axis=0)

		# Calculate skewness
		S1=stats.skew(data[i,:,:])

		# Calculate excess Kurtosis
		K1=stats.kurtosis(data[i,:,:])

		# Calculate percentiles
		p=[75,90,95]
		Pr1=np.array(np.percentile(data[i,:,:],p,axis=0)).T.flatten()

		# Percentile has 2*len(p) dimensions
		faux=np.hstack((Max1,Min1,M1,Md1,Std1,S1,K1,Pr1))
		#faux=np.hstack((M1,Std1,Pr1))
		features.append(faux)

	return(np.array(features),oClass)

def extractSilence(data,threshold=256):
	if(data[0]<=threshold):
		s=[1]
	else:
		s=[]
	for i in range(1,len(data)):
		if(data[i-1]>threshold and data[i]<=threshold):
			s.append(1)
		elif (data[i-1]<=threshold and data[i]<=threshold):
			s[-1]+=1
	# Returns array with silence times: [3, 5, 1, 6, 3, 10, 7, 3, 6, ...]
	return(s)

def extractFeaturesSilence(data,Class=0, threshold=256):
	features=[]
	nObs,nSamp,nCols=data.shape
	oClass=np.ones((nObs,1))*Class
	for i in range(nObs):
		silence_features=np.array([])
		for c in range(nCols):
			silence=extractSilence(data[i,:,c],threshold=threshold)
			# Append mean and variance of silences
			silence_features=np.append(silence_features,[np.mean(silence),np.var(silence)])
		
		features.append(silence_features)
		
	return(np.array(features),oClass)

def extractFeaturesWavelet(data,scales=[2,4,8,16,32],Class=0):
	features=[]
	nObs,nSamp,nCols=data.shape
	oClass=np.ones((nObs,1))*Class
	for i in range(nObs):
		scalo_features=np.array([])
		for c in range(nCols):
			scalo,scales=scalogram.scalogramCWT(data[i,:,c],scales)
			scalo_features=np.append(scalo_features,scalo)
			
		features.append(scalo_features)
		
	return(np.array(features),oClass)

def distance(c,p):
	return(np.sqrt(np.sum(np.square(p-c))))


def getMetrics(oClass, results):
	if DEBUG:
		print("Metrics:"+str(metrics.confusion_matrix(oClass[:, 0], results)))
	return metrics.confusion_matrix(oClass[:, 0], results)

def calculateFinalResults(results):
	return np.vstack((np.mean(np.diagonal(results)/np.sum(results, axis=0)), np.std(np.diagonal(results)/np.sum(results, axis=0), axis=0)))

def printFinalResults(title, metrics, results):
	print("\n** "+title+" results **")
	print("Confusion Matrix")
	print(metrics)
	print("Accuracy: "+str(results[0][0])+"  Standard Deviation: "+str(results[1][0])+"\n")

def main():

	SVC_metrics = []
	RBF_metrics = []
	SVC2_metrics = []
	Poly_metrics = []
	neural_network = []

	Classes = {0: "regularTraffic", 1: "Scenario1     ", 2: "Scenario2     ", 3: "Scenario3     "}

	regular_traffic = np.loadtxt('sensor1_results/out_sensor1_regular_l2_n1.txt')
	scenario_1 = np.loadtxt('sensor1_results/out_sensor1_s1_l2_n1.txt')
	scenario_2 = np.loadtxt('sensor1_results/out_sensor1_s2_l2_n1.txt')
	scenario_3 = np.loadtxt('sensor1_results/out_sensor1_s3_l2_n1.txt')


	regular_traffic_divided = getFullSampleSet(regular_traffic, random=random, sliding=sliding_windows, stepsize=sliding_window_size)
	scenario1_traffic_divided = getFullSampleSet(scenario_1, random=random, sliding=sliding_windows, stepsize=sliding_window_size)
	scenario2_traffic_divided = getFullSampleSet(scenario_2, random=random, sliding=sliding_windows, stepsize=sliding_window_size)
	scenario3_traffic_divided = getFullSampleSet(scenario_3, random=random, sliding=sliding_windows, stepsize=sliding_window_size)


	for iteration in range(numberIterations):
		if DEBUG:
			print("Iteration "+str(iteration+1))

		# Get the training and testing sets
		regular_test, regular_train = divideTrainingAndTestingSets(regular_traffic_divided, iteration, testPerc=1/numberIterations)
		scenario1_test, scenario1_train = divideTrainingAndTestingSets(scenario1_traffic_divided, iteration, testPerc=1/numberIterations)
		scenario2_test, scenario2_train = divideTrainingAndTestingSets(scenario2_traffic_divided, iteration, testPerc=1/numberIterations)
		scenario3_test, scenario3_train = divideTrainingAndTestingSets(scenario3_traffic_divided, iteration, testPerc=1/numberIterations)

		# Extract features for train set
		trainFeatures_regular, oClass_rt=extractFeatures(regular_train,Class=0)
		trainFeatures_scenario1, oClass_scenario1=extractFeatures(scenario1_train,Class=1)
		trainFeatures_scenario2, oClass_scenario2=extractFeatures(scenario2_train,Class=2)
		trainFeatures_scenario3, oClass_scenario3=extractFeatures(scenario3_train,Class=3)
		trainFeatures=np.vstack((trainFeatures_regular,trainFeatures_scenario1, trainFeatures_scenario2, trainFeatures_scenario3))
		trainFeatures = np.nan_to_num(trainFeatures)

		trainFeatures_regularS, oClass_rt=extractFeaturesSilence(regular_train, Class=0, threshold=silence_threshold)
		trainFeatures_scenario1S, oClass_scenario1=extractFeaturesSilence(scenario1_train, Class=1, threshold=silence_threshold)
		trainFeatures_scenario2S, oClass_scenario2=extractFeaturesSilence(scenario2_train, Class=2, threshold=silence_threshold)
		trainFeatures_scenario3S, oClass_scenario3=extractFeaturesSilence(scenario3_train, Class=3, threshold=silence_threshold)
		trainFeaturesS=np.vstack((trainFeatures_regularS, trainFeatures_scenario1S, trainFeatures_scenario2S, trainFeatures_scenario3S))
		trainFeaturesS = np.nan_to_num(trainFeaturesS)

		trainFeatures_regularW, oClass_rt=extractFeaturesWavelet(regular_train,scales,Class=0)
		trainFeatures_scenario1W, oClass_scenario1=extractFeaturesWavelet(scenario1_train,scales,Class=1)
		trainFeatures_scenario2W, oClass_scenario2=extractFeaturesWavelet(scenario2_train,scales,Class=2)
		trainFeatures_scenario3W, oClass_scenario3=extractFeaturesWavelet(scenario3_train,scales,Class=3)
		trainFeaturesW=np.vstack((trainFeatures_regularW, trainFeatures_scenario1W, trainFeatures_scenario2W, trainFeatures_scenario3W))
		trainFeaturesW = np.nan_to_num(trainFeaturesW)

		allTrainFeatures=np.hstack((trainFeatures,trainFeaturesS,trainFeaturesW))
		trainClass=np.vstack((oClass_rt,oClass_scenario1, oClass_scenario2, oClass_scenario3))


		# Extract features for test set
		testFeatures_regular, oClass_rt=extractFeatures(regular_test,Class=0)
		testFeatures_scenario1, oClass_scenario1=extractFeatures(scenario1_test,Class=1)
		testFeatures_scenario2, oClass_scenario2=extractFeatures(scenario2_test,Class=2)
		testFeatures_scenario3, oClass_scenario3=extractFeatures(scenario3_test,Class=3)
		testFeatures=np.vstack((testFeatures_regular, testFeatures_scenario1, testFeatures_scenario2, testFeatures_scenario3))
		testFeatures = np.nan_to_num(testFeatures)

		testFeatures_regularS, oClass_rt=extractFeaturesSilence(regular_test,Class=0, threshold=silence_threshold)
		testFeatures_scenario1S, oClass_scenario1=extractFeaturesSilence(scenario1_test,Class=1, threshold=silence_threshold)
		testFeatures_scenario2S, oClass_scenario2=extractFeaturesSilence(scenario2_test,Class=2, threshold=silence_threshold)
		testFeatures_scenario3S, oClass_scenario3=extractFeaturesSilence(scenario3_test,Class=3, threshold=silence_threshold)
		testFeaturesS=np.vstack((testFeatures_regularS, testFeatures_scenario1S, testFeatures_scenario2S, testFeatures_scenario3S))
		testFeaturesS = np.nan_to_num(testFeaturesS)

		testFeatures_regularW, oClass_rt=extractFeaturesWavelet(regular_test,scales,Class=0)
		testFeatures_scenario1W, oClass_scenario1=extractFeaturesWavelet(scenario1_test,scales,Class=1)
		testFeatures_scenario2W, oClass_scenario2=extractFeaturesWavelet(scenario2_test,scales,Class=2)
		testFeatures_scenario3W, oClass_scenario3=extractFeaturesWavelet(scenario3_test,scales,Class=3)
		testFeaturesW=np.vstack((testFeatures_regularW, testFeatures_scenario1W, testFeatures_scenario2W, testFeatures_scenario3W))
		testFeaturesW = np.nan_to_num(testFeaturesW)

		allTestFeatures=np.hstack((testFeatures,testFeaturesS,testFeaturesW))
		oClass=np.vstack((oClass_rt, oClass_scenario1, oClass_scenario2, oClass_scenario3))


		# Normalize data with mean=0 and variance=1
		scaler=StandardScaler()
		NormAllTrainFeatures=scaler.fit_transform(allTrainFeatures)
		NormAllTestFeatures=scaler.transform(allTestFeatures)


		# PCA for test and train features
		pca = PCA(n_components=10, svd_solver='full')


		NormTrainPcaFeatures = pca.fit(NormAllTrainFeatures).transform(NormAllTrainFeatures)
		NormTestPcaFeatures = pca.transform(NormAllTestFeatures)

		if DEBUG:
			colors=['b','g', 'r', 'y']

			nObs,nFea=NormTrainPcaFeatures.shape
			for i in range(nObs):
				plt.plot(NormTrainPcaFeatures[i,0],NormTrainPcaFeatures[i,1],'o'+colors[int(trainClass[i])])

			plt.figure()
			plt.show(block=False)

			nObs,nFea=NormAllTestFeatures.shape
			for i in range(nObs):
				plt.plot(NormAllTestFeatures[i,0],NormAllTestFeatures[i,1],'o'+colors[int(oClass[i])])

			plt.figure()
			plt.show(block=False)

		# Train classification algorithms
		svc = svm.SVC(kernel='linear').fit(NormTrainPcaFeatures, trainClass)  
		rbf_svc = svm.SVC(kernel='rbf').fit(NormTrainPcaFeatures, trainClass)  
		poly_svc = svm.SVC(kernel='poly',degree=2).fit(NormTrainPcaFeatures, trainClass)  
		lin_svc = svm.LinearSVC().fit(NormTrainPcaFeatures, trainClass)  

		L1=svc.predict(NormTestPcaFeatures)
		L2=rbf_svc.predict(NormTestPcaFeatures)
		L3=poly_svc.predict(NormTestPcaFeatures)
		L4=lin_svc.predict(NormTestPcaFeatures)

		if DEBUG:
			print('\n-- Classification based on Support Vector Machines  (PCA Features) --')
			nObsTest,nFea=NormTestPcaFeatures.shape
			for i in range(nObsTest):
				print('Obs: {:2}: SVC->{} | Kernel RBF->{} | Kernel Poly->{} | LinearSVC->{}'.format(i,Classes[L1[i]],Classes[L2[i]],Classes[L3[i]],Classes[L4[i]]))


		alpha=1
		max_iter=100000
		clf = MLPClassifier(solver='lbfgs',alpha=alpha,hidden_layer_sizes=(1000,),max_iter=max_iter)
		clf.fit(NormTrainPcaFeatures, trainClass) 
		LT=clf.predict(NormTestPcaFeatures) 

		if DEBUG:
			print('\n-- Classification based on Neural Networks --')
			nObsTest,nFea=NormTestPcaFeatures.shape
			for i in range(nObsTest):
				print('Obs: {:2}: Classification->{}'.format(i,Classes[LT[i]]))


		if DEBUG:
			print("\n** SVC **")
		metrics = getMetrics(oClass, L1)
		if SVC_metrics != []:
			SVC_metrics = np.vstack((SVC_metrics, metrics))
		else:
			SVC_metrics = metrics


		if DEBUG:
			print("\n** RBF SVC **")
		metrics = getMetrics(oClass, L2)
		if RBF_metrics != []:
			RBF_metrics = np.vstack((RBF_metrics, metrics))
		else:
			RBF_metrics = metrics


		if DEBUG:
			print("\n** Poly SVC **")
		metrics = getMetrics(oClass, L3)
		if Poly_metrics != []:
			Poly_metrics = np.vstack((Poly_metrics, metrics))
		else:
			Poly_metrics = metrics
		
		if DEBUG:
			print("\n** Linear SVC **")
		metrics = getMetrics(oClass, L4)
		if SVC2_metrics != []:
			SVC2_metrics = np.vstack((SVC2_metrics, metrics))
		else:
			SVC2_metrics = metrics
		

		if DEBUG:
			print("\n** Neural Network **")
		metrics = getMetrics(oClass, LT)
		if neural_network != []:
			neural_network = np.vstack((neural_network, metrics))
		else:
			neural_network = metrics
		
		if DEBUG:
			print("\n\n\n")

	
	SVC_metrics = np.sum(SVC_metrics.reshape(numberIterations, 4, 4), axis=0)
	SVC_results = calculateFinalResults(SVC_metrics)

	if DEBUG:
		print(SVC_metrics)
		print(SVC_results)

	RBF_metrics = np.sum(RBF_metrics.reshape(numberIterations, 4, 4), axis=0)
	RBF_results = calculateFinalResults(RBF_metrics)

	if DEBUG:
		print(RBF_metrics)
		print(RBF_results)

	Poly_metrics = np.sum(Poly_metrics.reshape(numberIterations, 4, 4), axis=0)
	Poly_results = calculateFinalResults(Poly_metrics)

	if DEBUG:
		print(Poly_metrics)
		print(Poly_results)

	SVC2_metrics = np.sum(SVC2_metrics.reshape(numberIterations, 4, 4), axis=0)
	SVC2_results = calculateFinalResults(SVC2_metrics)

	if DEBUG:
		print(SVC2_metrics)
		print(SVC2_results)

	neural_network = np.sum(neural_network.reshape(numberIterations, 4, 4), axis=0)
	neural_network_results = calculateFinalResults(neural_network)
	if DEBUG:
		print(neural_network)
		print(neural_network_results)


	printFinalResults("SVC", SVC_metrics, SVC_results)
	printFinalResults("RBF", RBF_metrics, RBF_results)
	printFinalResults("Poly", Poly_metrics, Poly_results)
	printFinalResults("Linear SVC Networks", SVC2_metrics, SVC2_results)
	printFinalResults("Neural Networks", neural_network, neural_network_results)


if __name__ == '__main__':
	main()


