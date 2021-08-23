//---------------------------------------//
// Define parameters.
//---------------------------------------//

// Define item parameters.
const item_set = 3;

// Define timing parameters.
const trial_duration = 30000;     // 30 seconds

// Define quality assurance parameters.
const max_threshold = 10;
const rg_threshold = 3000;       // 3 seconds

// Define screen size parameters.
var min_width = 640;
var min_height = 600;

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

// Iteratively construct trials.
items.forEach((j, i) => {

  // Define image metadata.
  const test_form  = form_order[i % 2];
  const distractor = (Math.random() < 0.5 ? 'md' : 'pd');

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

  // Define screen check.
  const screen_check = {
    timeline: [{
      type: 'screen-check',
      min_width: min_width,
      min_height: min_height
    }],
    conditional_function: function() {
      if (window.innerWidth >= min_width && window.innerHeight >= min_height) {
        return false;
      } else {
        return true;
      }
    }
  }

  // Define fixation.
  const fixation = {
    type: 'html-keyboard-response',
    stimulus: '',
    choices: jsPsych.NO_KEYS,
    trial_duration: 1200,
    on_start: function(trial) {
      const k = jsPsych.data.get().filter({trial_type:'mars', item_set: 3}).count();
      trial.stimulus = `<div style="font-size:24px;">Loading puzzle:<br>${k+1} / 16</div>`;
    }
  }

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

    }

  }

  // Define trial node.
  const trial_node = {
    timeline: [screen_check, fixation, trial]
  }

  // Push trial.
  MARS.push(trial_node);

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

//---------------------------------------//
// Define data quality check.
//---------------------------------------//

var QUALITY_CHECK = {
  type: 'call-function',
  func: function() {

    // Count number of rapid guessing trials.
    const rapid = jsPsych.data.get().filterCustom(function(trial) {
      return (trial.trial_type == 'mars' && trial.item_set == 3 && trial.rt != null && trial.rt < rg_threshold);
    }).count()

    // Count number of missing trials.
    const missing = jsPsych.data.get().filterCustom(function(trial) {
      return (trial.trial_type == 'mars' && trial.item_set == 3 && trial.rt == null);
    }).count()

    // Count number of screen minimized trials.
    const minimized = jsPsych.data.get().filter({trial_type: 'mars', item_set: 3, minimum_resolution: 0}).count();

    // Return summary scores.
    return [rapid, missing, minimized];

  },
  on_finish: function(trial) {

    // Extract data quality scores.
    const scores = jsPsych.data.getLastTrialData().values()[0].value;

    // Check if rejection warranted.
    if (scores.some((score) => score >= max_threshold)) {
      low_quality = true;
      jsPsych.endExperiment();
    }
  }
}

//---------------------------------------//
// Define feedback.
//---------------------------------------//

var FEEDBACK = {
  type: 'instructions',
  pages: [],
  show_clickable_nav: true,
  button_label_previous: 'Prev',
  button_label_next: 'Next',
  on_start: function(trial) {

    // Determine number of correct responses.
    const k = jsPsych.data.get().filter({trial_type: 'mars', item_set: 3, accuracy: 1}).count();

    // Define feedback page.
    trial.pages = [
      `<p>You got ${k} of 16 puzzles correct.</p><p>Click the "next" button below to continue.`
    ];

  }
}
