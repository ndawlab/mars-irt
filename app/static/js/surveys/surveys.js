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
    "I would prefer a task that is intellectual, difficult, and important to one that is important but does not require much thought.",

    // Infrequency item
    'Please select "uncertain" as your response for this statement.'

  ],
  scale: [
    "Extremely<br>uncharacteristic<br>of me",
    "Somewhat<br>uncharacteristic<br>of me",
    "Uncertain",
    "Somewhat<br>characteristic<br>of me",
    "Extremely<br>uncharacteristic<br>of me"
  ],
  reverse: [
    false, false, true, true, false, false, false
  ],
  instructions: 'For each of the statements below, please indicate whether or not the statement is characteristic of you or of what you believe.',
  survey_width: 950,
  item_width: 40,
  infrequency_items: [6],
  data: {survey: 'nfc6'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [1,1,0,1,1];
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
    "Rarely feel blue.",
    "Feel comfortable with myself.",
    "Am not easily bothered by things.",
    "Am very pleased with myself.",

    // Infrequency item
    "Can remember my own name."

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
  instructions: "The following are some phrases describing people's behaviors. Please use the rating scale to describe how accurately each statement describes you.",
  scale_repeat: 6,
  survey_width: 950,
  item_width: 40,
  infrequency_items: [10],
  data: {survey: 'neuroticism'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [1,1,1,0,0];
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
    "Tend to vote for conservative political candidates.",

    // Infrequency item
    "Can live for months without oxygen."

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
  instructions: "The following are some phrases describing people's behaviors. Please use the rating scale to describe how accurately each statement describes you.",
  scale_repeat: 6,
  survey_width: 950,
  item_width: 40,
  infrequency_items: [10],
  data: {survey: 'openness'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [0,0,1,1,1];
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
SURVEYS = SURVEYS.concat(infrequency_check)
