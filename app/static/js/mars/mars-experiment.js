//---------------------------------------//
// Define parameters.
//---------------------------------------//

// Define puzzle set.
var items = [1,2,3,4,5,6,7,8,9,10,11,12];
var shape_set = 1;
var distractor = 'pd';

// Define timing parameters.
const trial_duration = 30000;     // 30 seconds

// Define quality assurance parameters.
const max_threshold = 10;
const rg_threshold = 3000;        // 3 seconds

// Define screen size parameters.
var min_width = 600;
var min_height = 600;

//---------------------------------------//
// Define images for preloading.
//---------------------------------------//

var images_task = [];
items.forEach(i => {
  images_task.push(`../static/img/is3/mars_${i}_M_ss${shape_set}.jpeg`)
  images_task.push(`../static/img/is3/mars_${i}_T1_ss${shape_set}_${distractor}.jpeg`)
  images_task.push(`../static/img/is3/mars_${i}_T2_ss${shape_set}_${distractor}.jpeg`)
  images_task.push(`../static/img/is3/mars_${i}_T3_ss${shape_set}_${distractor}.jpeg`)
  images_task.push(`../static/img/is3/mars_${i}_T4_ss${shape_set}_${distractor}.jpeg`)
});

//---------------------------------------//
// Define MARS task.
//---------------------------------------//

// Preallocate space.
var MARS = [];

// Define image constants.
const img_path = `../static/img/is3/`;

// Iteratively construct trials.
items.forEach((j, i) => {

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
      const k = jsPsych.data.get().filter({trial_type: 'mars', item_set: 3}).count();
      trial.stimulus = `<div style="font-size:24px;">Loading puzzle:<br>${k+1} / 12</div>`;
    }
  }

  // Define trial.
  const trial = {
    type: 'mars',
    item: j,
    shape_set: shape_set,
    distractor: distractor,
    correct: 0,
    countdown: true,
    feedback: false,
    trial_duration: trial_duration,
    randomize_choice_order: true,
    img_path: img_path,
    data: {item_set: 3},
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
      `<p>You got ${k} of 12 puzzles correct.</p><p>Click the "next" button below to continue.`
    ];

  }
}
