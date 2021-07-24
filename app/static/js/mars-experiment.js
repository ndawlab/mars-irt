//---------------------------------------//
// Define parameters.
//---------------------------------------//

// Define item parameters.
const item_set = 3;

// Define timing parameters.
const trial_duration = 30000;     // 30 seconds

// Define quality assurance parameters.
const rg_threshold = 3000;       // 3 seconds
const rg_maximum = 5;
var rg_count = 0;

//---------------------------------------//
// Define puzzle set.
//---------------------------------------//

var items = [];
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([ 6, 19, 20, 22], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([25, 28, 39, 47], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([49, 50, 51, 61], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([65, 70, 71, 10], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([15, 11, 18, 13], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([27, 31, 34, 37], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([56, 58, 62, 69], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([77, 16, 17, 12], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([23, 40, 42, 53], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([60, 72, 73, 79], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([80, 14, 26, 52], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([59, 63, 67, 74], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([76, 36, 44, 46], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([54, 55, 64, 75], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([21, 24, 29, 30], 1));
items = items.concat(jsPsych.randomization.sampleWithoutReplacement([45, 78, 35, 66], 1));

//---------------------------------------//
// Define MARS task.
//---------------------------------------//

// Preallocate space.
var preload_mars = [];
var MARS = [];

// Define image constants.
const img_path = `../static/img/is${item_set}/`;
const form_order = (workerNo % 2 == 0) ? [1,2] : [2,1];
const dist_order = (Math.floor(workerNo / 2) == 0) ? ['md','pd'] : ['pd','md'];

// Iteratively construct trials.
items.forEach((j, i) => {

  // Define image metadata.
  const test_form  = form_order[i % 2];
  const distractor = dist_order[i % 2]

  // Define puzzle set order.
  if ( test_form == 1 ) {
    var ss = [3,1,2];
  } else if ( test_form == 2 ) {
    var ss = [2,3,1];
  } else if ( test_form == 3 ) {
    var ss = [1,2,3];
  }

  // Define images.
  const puzzle = img_path + `tf${test_form}/` + `tf${test_form}_${j}_M_ss${ss[(j-1)%3]}.jpeg`;
  const choices = [
    img_path + `tf${test_form}/` + `tf${test_form}_${j}_T1_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}/` + `tf${test_form}_${j}_T2_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}/` + `tf${test_form}_${j}_T3_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}/` + `tf${test_form}_${j}_T4_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
  ];

  // Append to preload cache.
  preload_mars = preload_mars.concat(puzzle);
  preload_mars = preload_mars.concat(choices);

  // Define trial.
  const trial = {
    type: 'mars',
    puzzle: puzzle,
    choices: choices,
    correct: 0,
    countdown: true,
    feedback: false,
    trial_duration: trial_duration,
    randomize_choice_order: true,
    data: {item_set: item_set, item: j, test_form: test_form, distractor: distractor},
    on_finish: function(data) {

      // Store number of browser interactions
      data.browser_interactions = jsPsych.data.getInteractionData().filter({trial: data.trial_index}).count();

      // Evaluate rapid guessing.
      if (data.rt < rg_threshold) {

        // Increment counter.
        rg_count++;

        //  Check if experiment should end.
        if (rg_count >= rg_maximum) {
          low_quality = true;
          jsPsych.endExperiment();
        }

      }

    }

  }

  // Push trial.
  MARS.push(trial);

});

// Randomize position order within each pair of items.
function swapElement(array, indexA, indexB) {
  var tmp = array[indexA];
  array[indexA] = array[indexB];
  array[indexB] = tmp;
}

const indices = [0,2,4,6,8,10,12,14]
indices.forEach((j, i) => {
  if (Math.random() < 0.5) { swapElement(MARS, j, j+1); }
});
