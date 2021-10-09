//------------------------------------//
// Define transition screens.
//------------------------------------//

// Welcome screen
var WELCOME = {
  type: 'instructions',
  pages: [
    "<b>Welcome to the study!</b><br><br>We will now get started with some surveys.<br>Please read each survey carefully and respond truthfully."
  ],
  show_clickable_nav: true,
  button_label_previous: 'Prev',
  button_label_next: 'Next'
}

//------------------------------------//
// Define questionnaires.
//------------------------------------//

// Demographics questionnaire
var DEMO = {
  type: 'survey-demo',
  data: {survey: 'demographics'}
};

// Need for cognition (abbreviated)
var nfc6 = {
  type: 'survey-template',
  items: [

    // Need for cognition
    "I would prefer complex to simple problems.",
    "I like to have the responsibility of handling a situation that requires a lot of thinking.",
    "Thinking is not my idea of fun.",
    "I would rather do something that requires little thought than something that is sure to challenge my thinking abilities.",
    "I really enjoy a task that involves coming up with new solutions to problems.",
    "I would prefer a task that is intellectual, difficult, and important to one that is somewhat important but does not require much thought."

    // Infrequency item
    "Worrying too much about the 1953 Olympics"

  ],
  scale: [
    "Extremely uncharacteristic of me",
    "Somewhat uncharacteristic of me",
    "Uncertain",
    "Somewhat characteristic of me",
    "Extremely uncharacteristic of me"
  ],
  reverse: [
    false, false, false, false, false, false, false
  ],
  instructions: 'For each of the statements below, please indicate whether or not the statement is characteristic of you or of what you believe.',
  survey_width: 950,
  item_width: 40,
  infrequency_items: [6],
  data: {survey: 'nfc6'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [0,1,1,1];
    data.infrequency = scores[data.responses['Q07']];

  }
}

// IPIP NEO-PI-R Neuroticism
var neuroticism = {
  type: 'survey-template',
  items: [

    // Neuroticism beliefs (forward-scored)
    "Often feel blue.",
    "Dislike myself.",
    "Am often down in the dumps.",
    "Have frequent mood swings.",
    "Panic easily.",

    // Neuroticism beliefs (reverse-scored)
    "Rarely get irritated.",
    "Seldom feel blue.",
    "Feel comfortable with myself.",
    "Am not easily bothered by things.",
    "Am very pleased with myself."

    // Infrequency item
    "I am usually able to remember my own name."

  ],
  scale: [
    "Disagree",
    "Slightly disagree",
    "Neutral",
    "Slightly agree",
    "Agree"
  ],
  reverse: [
    false, false, false, false, false, true, true, true, true, true, false
  ],
  instructions: 'Select the option that best describes how typical or characteristic each item is of you.',
  survey_width: 950,
  item_width: 40,
  infrequency_items: [8],
  data: {survey: 'neuroticism'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [1,1,1,0.5,0];
    data.infrequency = scores[data.responses['Q11']];

  }

}

// IPIP NEO-PI-R Openness to Experience
var openness = {
  type: 'survey-template',
  items: [

    // Openness beliefs (forward-scored)
    "Believe in the importance of art.",
    "Have a vivid imagination.",
    "Tend to vote for liberal political candidates.",
    "Carry the conversation to a higher level.",
    "Enjoy hearing new ideas.",

    // Openness beliefs (reverse-scored)
    "Am not interested in abstract ideas.",
    "Do not like art.",
    "Avoid philosophical discussions.",
    "Do not enjoy going to art museums.",
    "Tend to vote for conservative political candidates."

    // Infrequency item
    "Believe that I need food and water to stay alive."

  ],
  scale: [
    "Disagree",
    "Slightly disagree",
    "Neutral",
    "Slightly agree",
    "Agree"
  ],
  reverse: [
    false, false, false, true, true, true, true, true, true, true, false
  ],
  instructions: "The following are phrases that describe people's behaviors. Indicate how accurately each statement describes you. Describe yourself as you generally are now, not as you wish to be in the future.",
  scale_repeat: 6,
  survey_width: 900,
  item_width: 40,
  infrequency_items: [10],
  data: {survey: 'openness'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [1,1,0.5,0,0];
    data.infrequency = scores[data.responses['Q11']];

  }
}

//------------------------------------//
// Define quality check
//------------------------------------//
// Check responses to infrequency items. Reject participants
// who respond carelessly on all 3 items.

// Define infrequency item check.
var score_infrequency_items = function() {

  // Score infrequency items.
  const infreq = jsPsych.data.get().select('infrequency').sum();
  const sl = jsPsych.data.get().select('straightlining').sum();
  const zz = jsPsych.data.get().select('zigzagging').sum();
  return [infreq, sl, zz];

}

var infrequency_check = {
  type: 'call-function',
  func: score_infrequency_items,
  on_finish: function(trial) {
    if (jsPsych.data.getLastTrialData().values()[0].value[0] >= 2) {
      low_quality = true;
      jsPsych.endExperiment();
    }
  }
}

//------------------------------------//
// Define survey block
//------------------------------------//

// Define survey block
var SURVEYS = jsPsych.randomization.shuffle([nfc6, neuroticism, openness]);
