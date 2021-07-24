//---------------------------------------//
// Define parameters.
//---------------------------------------//

// Define item set.
const item_set = 3;               // Available [1,2,3]

// Define test form.
const test_form = 1;              // Available [1,2,3]

// Define distractor set.
const distractor = 'pd';          // Available [md, pd]

// Define timing parameters.
const trial_duration = 30000;     // 30 seconds

//---------------------------------------//
// Define minimal stimulus set.
//---------------------------------------//

var stimuli = [];
stimuli = stimuli.concat( Math.random() < 0.5 ? [ 1,  6] : [19, 20] );    // Dimension = 2
stimuli = stimuli.concat( Math.random() < 0.5 ? [15, 10] : [11, 18] );    // Dimension = 3
stimuli = stimuli.concat( Math.random() < 0.5 ? [16, 17] : [12, 23] );    // Dimension = 4
stimuli = stimuli.concat( Math.random() < 0.5 ? [14, 26] : [52, 59] );    // Dimension = 5
// stimuli = jsPsych.randomization.shuffle(stimuli);

//---------------------------------------//
// Define MARS task.
//---------------------------------------//

// Define path to stimuli.
const img_path = '../static/img/is' + item_set + '/tf' + test_form + '/';

// Define stimulus set order.
if ( test_form == 1 ) {
  var ss = [3,1,2];
} else if ( test_form == 2 ) {
  var ss = [2,3,1];
} else if ( test_form == 3 ) {
  var ss = [1,2,3];
}

// Initialize timeline.
var preload_mars = [];
var MARS = [];

// Iteratively
stimuli.forEach((j, i) => {

  // Define images.
  const stimulus = img_path + `tf${test_form}_${j}_M_ss${ss[(j-1)%3]}.jpeg`;
  const choices = [
    img_path + `tf${test_form}_${j}_T1_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}_${j}_T2_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}_${j}_T3_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
    img_path + `tf${test_form}_${j}_T4_ss${ss[(j-1)%3]}_${distractor}.jpeg`,
  ];

  // Append to preload cache.
  preload_mars = preload_mars.concat(stimulus);
  preload_mars = preload_mars.concat(choices);

  // Define trial.
  const trial = {
    type: 'mars',
    stimulus: stimulus,
    choices: choices,
    correct: 0,
    countdown: true,
    feedback: true,
    trial_duration: trial_duration,
    randomize_choice_order: true,
    data: { item_set: item_set, test_form: test_form, distractor: distractor }
  }

  // Push trial.
  MARS.push(trial);

});
