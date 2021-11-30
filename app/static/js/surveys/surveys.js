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
var nfc10 = {
  type: 'survey-template',
  items: [

    // Need for cognition
    "I would prefer complex to simple problems.",
    "I like to have the responsibility of handling a situation that requires a lot of thinking.",
    "Thinking is not my idea of fun.",
    "I would rather do something that requires little thought than something that is sure to challenge my thinking abilities.",
    "I try to anticipate and avoid situations where there is a likely chance I will have to think in depth about something.",
    "I find satisfaction in deliberating hard and for long hours.",
    "The idea of relying on thought to make my way to the top appeals to me.",
    "I really enjoy a task that involves coming up with new solutions to problems.",
    "I prefer my life to be filled with puzzles I must solve.",
    "I would prefer a task that is intellectual, difficult, and important to one that is somewhat important but does not require much thought.",

    // Infrequency item
    "I am able to stop breathing entirely for weeks without the aid of medical equipment."

  ],
  scale: [
    "Extremely<br>uncharacteristic<br>of me",
    "Somewhat<br>uncharacteristic<br>of me",
    "Uncertain",
    "Somewhat<br>characteristic<br>of me",
    "Extremely<br>characteristic<br>of me"
  ],
  reverse: [
    false, false, true, true, true, false, false, false, false, false, false
  ],
  instructions: 'For each of the statements below, please indicate whether or not the statement is characteristic of you or of what you believe.',
  scale_repeat: 6,
  survey_width: 950,
  item_width: 40,
  infrequency_items: [10],
  data: {survey: 'nfc10'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [0,0.5,1,1,1];
    data.infrequency = scores[data.responses['Q11']];

  }
}

// PROMIS cognitive function - short form 8a
var pcf = {
  type: 'survey-template',
  items: [

    // Cognitive functioning
    "My thinking has been slow.",
    "It has seemed like my brain was not working as well as usual.",
    "I have had to work harder than usual to keep track of what I was doing.",
    "I have had trouble shifting back and forth between different activities that require thinking.",
    "I have had trouble concentrating.",
    "I have had to work really hard to pay attention or I would make a mistake.",
    "I have had trouble forming thoughts.",
    "I have had trouble adding or subtracting numbers in my head.",

    // Infrequency item
    "I was able to remember my own name."

  ],
  scale: [
    "Never",
    "Rarely",
    "Sometimes",
    "Often",
    "Very often"
  ],
  reverse: [
    true, true, true, true, true, true, true, true, false
  ],
  instructions: 'For each of the statements below, please indicate how much the statement has applied to you <b>over the last 7 days</b>.',
  scale_repeat: 5,
  survey_width: 950,
  item_width: 40,
  infrequency_items: [9],
  data: {survey: 'pcf'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [1,1,1,0.5,0];
    data.infrequency = scores[data.responses['Q09']];

  }

}

// Subjective numeracy scale
var sns = {
  type: 'survey-likert',
  questions: [
    {
      prompt: "How good are you at working with fractions?",
      labels: ["Not at all<br>good", "", "", "", "", "Extremely<br>good"],
      required: true
    },
    {
      prompt: "How good are you at working with percentages?",
      labels: ["Not at all<br>good", "", "", "", "", "Extremely<br>good"],
      required: true
    },
    {
      prompt: "How good are you at calculating a 15% tip?",
      labels: ["Not at all<br>good", "", "", "", "", "Extremely<br>good"],
      required: true
    },
    {
      prompt: "How good are you at figuring out how much a shirt will cost if it is 25% off?",
      labels: ["Not at all<br>good", "", "", "", "", "Extremely<br>good"],
      required: true
    },
    {
      prompt: "When reading the newspaper, how helpful do you find tables and graphs that are parts of a story?",
      labels: ["Not at all<br>helpful", "", "", "", "", "Extremely<br>helpful"],
      required: true
    },
    {
      prompt: `When people tell you the chance of something happening, do you prefer that they<br> use words ("it rarely happens") or numbers ("there's a 1% chance")?`,
      labels: ["Always Prefer<br>Words", "", "", "", "", "Always Prefer<br>Numbers"],
      required: true
    },
    {
      prompt: `When you hear a weather forecast, do you prefer predictions using percentages (e.g., "there will<br>be a 20% chance of rain today") or predictions using only words (e.g., "there is a small chance<br>of rain today")?`,
      labels: ["Always Prefer<br>Percentages", "", "", "", "", "Always Prefer<br>Words"],
      required: true
    },
    {
      prompt: "How often do you find numerical information to be useful?",
      labels: ["Never", "", "", "", "", "Very Often"],
      required: true
    },
    {
      prompt: 'Please select "Never" as your response for this statement.',
      labels: ["Never", "", "", "", "", "Very Often"],
      required: true
    },
  ],
  scale_width: 700,
  autocomplete: false,
  randomize_question_order: true,
  data: {survey: 'sns'},
  on_finish: function(data) {

    // Score response on infrequncy item.
    const scores = [0,1,1,1,1,1];
    data.infrequency = scores[data.response['Q8']];

  }
}

//------------------------------------//
// Define quality check
//------------------------------------//
// Check responses to infrequency items. Reject participants
// who respond carelessly on all 3 items.

// Define infrequency item check.
var score_infrequency_items = function() {
  return jsPsych.data.get().select('infrequency').sum();
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
var SURVEYS = jsPsych.randomization.shuffle([nfc10, pcf, sns]);
SURVEYS = SURVEYS.concat(infrequency_check)
