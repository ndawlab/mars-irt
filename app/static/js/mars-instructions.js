//---------------------------------------//
// Define parameters.
//---------------------------------------//

// Define image scaling CSS.
const style = "width:auto; height:auto; max-width:100%; max-height:200px;";

//---------------------------------------//
// Define instructions screens.
//---------------------------------------//

var instructions_01 = {
  type: 'instructions',
  pages: [
    `<p>In this task, you will be shown a 3x3 grid of patterns. The last one, in the bottom right-hand corner, <b>will be missing:</b></p><img src="../static/img/practice/p1_M1.png" style="${style}"</img><p>You will need to select <b>which of the four possible patterns</b> along the bottom <b>fits into the gap</b>:</p><img src="../static/img/practice/p1_T1.png" style="${style}"</img>`,
    '<p>Try to be as accurate as you can be.</p><p>If you cannot solve the puzzle then you should guess - you will not be penalized for an incorrect answer.</p><p>The task contains a shuffled mix of easy, medium and hard puzzles.</p><p>You will have <b>30 seconds</b> to complete each puzzle.</p>',
    '<p>Now, we will practice on three puzzles.</p><p>Press the "next" button to get started.</p>'

  ],
  show_clickable_nav: true,
  button_label_previous: 'Prev',
  button_label_next: 'Next',
  on_start: function(trial) {
    pass_message('starting instructions');
  }
}

var instructions_02 = {
  type: 'instructions',
  pages: [
    '<p>Great job! Now you understand what to do.</p>',
    '<p>Now, we will move onto the real puzzles.</p><p>There are 16 puzzles in total. You will have <b>30 seconds</b> to complete each one.<br>For these puzzles, you will <u>not</u> receive feedback after you make your choice.</p><p>At the end of the game, your total number of correct answers will be converted<br>into a <b>performance bonus</b>. So try your hardest to solve the puzzles! </p><p>Press the "next" button to get started.</p>'
  ],
  show_clickable_nav: true,
  button_label_previous: 'Prev',
  button_label_next: 'Next',
  on_finish: function(trial) {
    pass_message('starting mars');
  }
}

//---------------------------------------//
// Define practice block.
//---------------------------------------//

// Preallocate space.
const practice_block = [];
var preload_practice = [];

// Iteratively add trials.
for (let i = 0; i < 3; i++) {

  // Define images.
  const puzzle = `../static/img/practice/pt${i+1}_M1.png`;
  const choices = [
    `../static/img/practice/pt${i+1}_T1.png`,
    `../static/img/practice/pt${i+1}_T2.png`,
    `../static/img/practice/pt${i+1}_T3.png`,
    `../static/img/practice/pt${i+1}_T4.png`,
  ];

  // Append to preload cache.
  preload_practice = preload_practice.concat(puzzle);
  preload_practice = preload_practice.concat(choices);

  // Define trial.
  const practice_trial = {
    type: 'mars',
    puzzle: puzzle,
    choices: choices,
    correct: 0,
    countdown: true,
    feedback: true,
    feedback_duration: 2000,
    incorrect_feedback: '<p style="font-size: 18px">Not quite! Look carefully - can you spot a pattern?</p>',
    trial_duration: 30000,
    randomize_choice_order: true,
    data: { item_set: 'practice' }
  }

  // Define looping node.
  const practice_trial_node = {
    timeline: [practice_trial],
    loop_function: function(data) {
      if ( data.values()[0].accuracy == 1 ){
        return false;
      } else {
        return true;
      }
    }
  }

  // Push trial.
  practice_block.push(practice_trial_node);

}

//---------------------------------------//
// Define instructions timeline.
//---------------------------------------//

// Define instructions timeline.
var INSTRUCTIONS = [];
INSTRUCTIONS = INSTRUCTIONS.concat(instructions_01);
INSTRUCTIONS = INSTRUCTIONS.concat(practice_block);
INSTRUCTIONS = INSTRUCTIONS.concat(instructions_02);
