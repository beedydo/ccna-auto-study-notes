// T42 macro: runs ON the RoomOS device (Macro Editor), not on your laptop.
// Uses all four xAPI types. Not runnable here: needs a real device with macros enabled
// (xConfiguration Macros Mode: On).
import xapi from 'xapi';

const MAX = 70;

async function start() {
  await xapi.Config.Audio.DefaultVolume.set(50);                   // xConfiguration: a setting

  const level = await xapi.Status.Audio.Volume.get();               // xStatus: current state
  console.log(`Volume at boot: ${level}`);

  xapi.Status.Audio.Volume.on((value) => {                          // xStatus change feedback
    if (Number(value) > MAX) {
      xapi.Command.Audio.Volume.Set({ Level: MAX });                // xCommand: an action
    }
  });

  xapi.Event.CallDisconnect.on((event) => {                         // xEvent: something happened
    console.log(`Call ended: ${event.CauseType}`);
    xapi.Command.UserInterface.Message.Alert.Display({ Title: 'NOC', Text: 'Call ended', Duration: 5 });
  });
}

start();
