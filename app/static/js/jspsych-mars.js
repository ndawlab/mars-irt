/**
 * jspsych-mars
 * Sam Zorowitz
 *
 * plugin for one trial of the matrix reasoning item bank (MaRs-IB)
 *
 * documentation: http://dx.doi.org/10.1098/rsos.190232
 *
 **/

jsPsych.plugins["mars"] = (function() {

  var plugin = {};

  plugin.info = {
    name: 'mars',
    description: '',
    parameters: {
      stimulus: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Stimulus',
        description: 'The HTML string to be displayed'
      },
      choices: {
        type: jsPsych.plugins.parameterType.STRING,
        pretty_name: 'Choices',
        array: true,
        description: 'The labels for the buttons.'
      },
      correct: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Correct',
        description: 'The index of the correct response.'
      },
      countdown: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Countdown',
        default: true,
        description: 'If true, the countdown timer will be presented (last 5s).'
      },
      feedback: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Feedback',
        default: true,
        description: 'If true, accuracy feedback will be presented.'
      },
      correct_feedback: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Correct feedback',
        default: null,
        description: 'Feedback to display following a correct choice.'
      },
      incorrect_feedback: {
        type: jsPsych.plugins.parameterType.HTML_STRING,
        pretty_name: 'Incorrect feedback',
        default: null,
        description: 'Feedback to display following an incorrect choice.'
      },
      trial_duration: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Trial duration',
        default: null,
        description: 'How long to show the trial.'
      },
      feedback_duration: {
        type: jsPsych.plugins.parameterType.INT,
        pretty_name: 'Feedback duration',
        default: 750,
        description: 'How long to show the feedback.'
      },
      randomize_choice_order: {
        type: jsPsych.plugins.parameterType.BOOL,
        pretty_name: 'Randomize choice order',
        default: false,
        description: 'If true, the order of the choices will be randomized.'
      }
    }
  }

  plugin.trial = function(display_element, trial) {

    //---------------------------------------//
    // Define HTML.
    //---------------------------------------//

    // Initialize HTML.
    var new_html = '';

    // Insert CSS.
    new_html += `<style>
    body {
      height: 100vh;
      max-height: 100vh;
      overflow: hidden;
      position: fixed;
    }
    p {
      margin-block-start: 15px;
      margin-block-end: 0;
    }
    .mars-container {
      width: 100vw;
      height: 100vh;
    }
    .mars-grid {

      /* Grid position */
      position: absolute;
      left: 50%;
      top: 60px;
      -webkit-transform: translateX(-50%);
      transform: translateX(-50%);

      /* Grid size */
      width: 100vw;
      height: calc(100vh - 60px);

      /* Grid parameters */
      display: grid;
      grid-template-columns: auto;
      grid-template-rows: 45vh 10vh 16vh;
      grid-row-gap: 2vh;
      justify-content: center;

    }
    .mars-item {

      /* Stimulus position */
      position: relative;

    }
    .mars-item img {

      /* Stimulus size */
      width:  auto;
      height: auto;
      max-width: 100%;
      max-height: 44vh;

      /* Stimulus aesthetics */
      border: 5px solid #777777;
      border-radius: 2px;
      padding: 5px;

    }
    .mars-choice-row {

      /* Grid position */
      position: relative;

      /* Grid parameters */
      display: grid;
      grid-template-columns: 25% 25% 25% 25%;
      grid-template-rows: auto;
      justify-content: center;
      align-items: center;

      /* Grid spacing */
      grid-column-gap: 25px;

    }
    .mars-choice-row .mars-choice {

      /* Choice position */
      display: grid;
      justify-content: center;
      align-items: center;

      /* Choice size */
      width: 100%;
      height: 100%;

    }
    .mars-choice-row .mars-choice img {

      /* Stimulus size */
      width:  auto;
      height: auto;
      max-width: 100%;
      max-height: 16vh;

      /* Stimulus aesthetics */
      box-sizing: border-box;
      border: 2px solid #777777;
      border-radius: 4px;
      padding: 2px;

    }
    .mars-choice-row .mars-choice img:hover {
      border: 2px solid #222222;
    }
    </style>`;

    // Initialize container.
    new_html += '<div class="mars-container">';
    new_html += '<div class="mars-grid">';

    // Display stimulus.
    new_html += '<div class="mars-item">';
    new_html += `<img src="${trial.stimulus}">`;
    new_html += '</div>';

    // Randomize choice order.
    var item_order = [...Array(trial.choices.length).keys()];
    if (trial.randomize_choice_order) {
       item_order = jsPsych.randomization.shuffle(item_order);
    }

    // Display feedback.
    new_html += '<div class="mars-item" id="feedback"></div>';

    // Display responses.
    new_html += '<div class="mars-item">';
    new_html += '<div class="mars-choice-row">';
    item_order.forEach((i) => {
      new_html += `<div class="mars-choice" id="jspsych-mars-choice-${i}" choice="${i}">`;
      new_html += `<img src="${trial.choices[i]}">`;
      new_html += '</div>';
    })
    new_html += '</div>';
    new_html += '</div>';

    // Close containers.
    new_html += '</div>';
    new_html += '</div>';

    display_element.innerHTML = new_html;

    //---------------------------------------//
    // Response handling.
    //---------------------------------------//

    // confirm screen resolution
    const screen_resolution = [window.screen.height, window.screen.width];
    const mediaQuery = window.matchMedia('(min-height: 300px) and (min-width: 800px)');

    // start time
    var start_time = performance.now();

    // add event listeners to buttons
    for (var i = 0; i < trial.choices.length; i++) {
      display_element.querySelector('#jspsych-mars-choice-' + i).addEventListener('click', function(e){
        var choice = e.currentTarget.getAttribute('choice');
        after_response(choice);
      });
    }

    // define feedback
    if ( trial.correct_feedback == null ) {
      trial.correct_feedback = '<p style="color: green; font-size: 10vh;">&#10003</p>';
    }
    if ( trial.incorrect_feedback == null ) {
      trial.incorrect_feedback = '<p style="color: red; font-size: 10vh;">&#10007</p>';
    }

    // store response
    var response = {
      rt: null,
      choice: null,
      accuracy: null
    };

    // function to display remaining time
    function countdown(t) {
      display_element.querySelector('#feedback').innerHTML = `${t}`;
      display_element.querySelector('#feedback').style['font-size'] = '6vh';
    };

    // function to handle responses by the subject
    function after_response(choice) {

      // kill any remaining setTimeout handlers
      jsPsych.pluginAPI.clearAllTimeouts();

      // measure response time
      var end_time = performance.now();
      var rt = end_time - start_time;

      // store responses.
      response.rt = rt;
      response.choice = parseInt(choice);
      response.accuracy = (trial.correct == response.choice) ? 1 : 0;

      // present feedback
      if ( trial.feedback && response.accuracy == 1 ) {
        display_element.querySelector('#feedback').innerHTML = trial.correct_feedback;
      } else if ( trial.feedback && response.accuracy == 0 ) {
        display_element.querySelector('#feedback').innerHTML = trial.incorrect_feedback;
      }

      // feedback timeout
      jsPsych.pluginAPI.setTimeout(function() {
        end_trial();
      }, trial.feedback ? trial.feedback_duration : 0);

    };

    // function to end trial when it is time
    function end_trial() {

      // kill any remaining setTimeout handlers
      jsPsych.pluginAPI.clearAllTimeouts();

      // gather the data to store for the trial
      var trial_data = {
        stimulus: trial.stimulus,
        correct: trial.correct,
        choice: response.choice,
        accuracy: response.accuracy,
        rt: response.rt,
        screen_resolution: screen_resolution,
        minimum_resolution: (mediaQuery.matches) ? 1 : 0
      };

      // clear the display
      display_element.innerHTML = '';

      // move on to the next trial
      jsPsych.finishTrial(trial_data);
    };

    // end trial if time limit is set
    if (trial.trial_duration !== null) {

      // initiate counter to end trial
      jsPsych.pluginAPI.setTimeout(function() {
        end_trial();
      }, trial.trial_duration);

      // initiate countdown timers
      if (trial.countdown) {
        for (let i = 1; i <= 5; i++) {
          jsPsych.pluginAPI.setTimeout(function() {
            countdown(i);
          }, trial.trial_duration - i*1000);
        }
      }

    }

  };

  return plugin;
})();
