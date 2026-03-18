const OFFSET = 24 + 45 + (44 + 87); // = 200

function decode(message) {
  return message.replace(/./g, function(char, position) {
    return String.fromCharCode(
      ((char.charCodeAt(0) * position) + OFFSET) % 77 + 48
    );
  });
}

console.log(decode('SywSqpJUmN6K2y8Jy2LQbZMfDbotaXmzzUHmKRdthivrzHvpwgEvuHWegRVB5CZ6O5Nl13EaWxYjMGf8Wc0yUvauqyqTr18ZDMTI'));