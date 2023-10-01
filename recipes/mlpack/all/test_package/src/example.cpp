// Define these to print extra informational output and warnings.
#define MLPACK_PRINT_INFO
#define MLPACK_PRINT_WARN
#include <mlpack.hpp>

using namespace arma;
using namespace mlpack;
using namespace mlpack::tree;
using namespace std;

int main()
{
  // Load the datasets.
  mat dataset = {
      { 3493,16,14,660,145,4313,207,209,137,3453,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0 },
      { 2917,4,15,525,135,1273,199,209,146,2250,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0 },
      { 3281,64,13,420,153,1473,232,212,110,2163,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0 },
      { 3021,90,14,0,0,3920,241,217,103,2583,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0 },
      { 3287,28,10,323,84,5074,216,217,136,182,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0 }
  };
  Row<size_t> labels = {
    7,
    2,
    2,
    1,
    1,
    2,
    1,
    2,
    3,
    6,
    2,
    3,
    2,
    1,
    2,
    1,
    1,
    2,
    2,
    2,
    2,
    2,
    1,
    2,
    1,
    2,
    2,
    2,
    5,
    2,
    2,
    2,
    1,
    6,
    1,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    1,
    1,
    2,
    1,
    3,
    2,
    2,
    1,
    5,
    2,
    2,
    1,
  };

  // Labels are 1-7, but we want 0-6 (we are 0-indexed in C++).
  labels -= 1;

  // Now split the dataset into a training set and test set, using 30% of the
  // dataset for the test set.
  mat trainDataset, testDataset;
  Row<size_t> trainLabels, testLabels;
  data::Split(dataset, labels, trainDataset, testDataset, trainLabels,
      testLabels, 0.3);

  // Create the RandomForest object and train it on the training data.
  RandomForest<> r(trainDataset,
                   trainLabels,
                   7 /* number of classes */,
                   10 /* number of trees */,
                   3 /* minimum leaf size */);

  // Compute and print the training error.
  Row<size_t> trainPredictions;
  r.Classify(trainDataset, trainPredictions);
  const double trainError =
      arma::accu(trainPredictions != trainLabels) * 100.0 / trainLabels.n_elem;
  cout << "Training error: " << trainError << "%." << endl;

  // Now compute predictions on the test points.
  Row<size_t> testPredictions;
  r.Classify(testDataset, testPredictions);
  const double testError =
      arma::accu(testPredictions != testLabels) * 100.0 / testLabels.n_elem;
  cout << "Test error: " << testError << "%." << endl;
}
