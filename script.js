/* ============================================================
   MITHRA — Man Ka Mitra AI
   Application logic

   Everything is kept client-side on purpose: the account and the
   conversation live in localStorage and never leave the device.
   Passwords are stored as a salted SHA-256 digest rather than in
   the clear. That is not a substitute for a real backend, but it
   means a stray glance at devtools does not hand over a password
   people probably reuse elsewhere.
   ============================================================ */

(function () {
  'use strict';

  /* ----------------------------------------------------------
     Configuration
     ---------------------------------------------------------- */

  var KEYS = {
    accounts: 'mithra.accounts',
    session: 'mithra.session',
    thread: 'mithra.thread',
    language: 'mithra.language',
    diary: 'mithra.diary'
  };

  var SPLASH_MS = 2200;
  var MIN_PASSWORD = 8;
  var HELPLINE = 'Tele-MANAS, 14416';

  var APP_VIEWS = ['home', 'language', 'chat', 'diary', 'profile'];

  /* Views that are not tabs still light up the tab they sit under. */
  var TAB_FOR = { chat: 'home', language: 'home' };


  /* ----------------------------------------------------------
     Small helpers
     ---------------------------------------------------------- */

  function $(selector, scope) {
    return (scope || document).querySelector(selector);
  }

  function $all(selector, scope) {
    return Array.prototype.slice.call((scope || document).querySelectorAll(selector));
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function clockTime(stamp) {
    return new Date(stamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function calendarDate(stamp) {
    return new Date(stamp).toLocaleDateString([], {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  }


  /* ----------------------------------------------------------
     Storage
     Wrapped because private browsing modes and full quotas both
     throw on write, and a blown-up login screen helps no one.
     ---------------------------------------------------------- */

  /* Some browsers (private tabs, in-app webviews, sandboxed
     previews) throw the first time localStorage is touched at
     all. Once that happens there's no point trying it again for
     the rest of this tab — an in-memory table keeps sign-up and
     login working for the session instead of every call failing
     from then on. */
  var persistent = true;
  var memoryTable = {};

  var store = {
    read: function (key, fallback) {
      if (!persistent) {
        return Object.prototype.hasOwnProperty.call(memoryTable, key)
          ? memoryTable[key]
          : fallback;
      }

      try {
        var raw = localStorage.getItem(key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch (err) {
        persistent = false;
        return this.read(key, fallback);
      }
    },

    write: function (key, value) {
      if (!persistent) {
        memoryTable[key] = value;
        return true;
      }

      try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
      } catch (err) {
        persistent = false;
        return this.write(key, value);
      }
    },

    drop: function (key) {
      if (!persistent) {
        delete memoryTable[key];
        return;
      }

      try {
        localStorage.removeItem(key);
      } catch (err) {
        persistent = false;
        delete memoryTable[key];
      }
    }
  };


  /* ----------------------------------------------------------
     Password hashing
     crypto.subtle needs a secure context, which a file:// page
     does not always get. The fallback is weak but it keeps the
     app working when the page is opened straight off disk.
     ---------------------------------------------------------- */

  function randomSalt() {
    var bytes = new Uint8Array(16);

    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(bytes);
    } else {
      for (var i = 0; i < bytes.length; i++) {
        bytes[i] = Math.floor(Math.random() * 256);
      }
    }

    return Array.prototype.map
      .call(bytes, function (b) { return b.toString(16).padStart(2, '0'); })
      .join('');
  }

  function weakDigest(value) {
    var hash = 5381;

    for (var i = 0; i < value.length; i++) {
      hash = ((hash << 5) + hash + value.charCodeAt(i)) >>> 0;
    }

    return 'fb$' + hash.toString(16);
  }

  function hashPassword(password, salt) {
    var payload = salt + '::' + password;

    if (!window.crypto || !window.crypto.subtle) {
      return Promise.resolve(weakDigest(payload));
    }

    var bytes = new TextEncoder().encode(payload);

    return window.crypto.subtle
      .digest('SHA-256', bytes)
      .then(function (buffer) {
        return Array.prototype.map
          .call(new Uint8Array(buffer), function (b) {
            return b.toString(16).padStart(2, '0');
          })
          .join('');
      })
      .catch(function () {
        return weakDigest(payload);
      });
  }


  /* ----------------------------------------------------------
     Toast
     ---------------------------------------------------------- */

  var toastNode = $('#toast');
  var toastTimer = null;

  function toast(message, tone) {
    if (!toastNode) return;

    clearTimeout(toastTimer);

    toastNode.textContent = message;
    toastNode.dataset.tone = tone || 'neutral';
    toastNode.classList.add('is-open');

    toastTimer = setTimeout(function () {
      toastNode.classList.remove('is-open');
    }, 2800);
  }


  /* ----------------------------------------------------------
     Validation
     ---------------------------------------------------------- */

  var EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[a-z]{2,}$/i;

  function setError(inputId, message) {
    var input = document.getElementById(inputId);
    var slot = $('[data-error-for="' + inputId + '"]');

    if (input) input.setAttribute('aria-invalid', message ? 'true' : 'false');
    if (slot) slot.textContent = message || '';
  }

  function clearErrors(form) {
    $all('.field__error', form).forEach(function (slot) { slot.textContent = ''; });
    $all('input', form).forEach(function (input) {
      input.setAttribute('aria-invalid', 'false');
    });
  }

  function focusFirstError(form) {
    var broken = $('input[aria-invalid="true"]', form);
    if (broken) broken.focus();
  }

  /* Returns 0-4. Length matters most, variety second. */
  function passwordStrength(password) {
    if (!password) return 0;

    var score = 0;

    if (password.length >= MIN_PASSWORD) score++;
    if (password.length >= 12) score++;
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score++;
    if (/\d/.test(password) && /[^\w\s]/.test(password)) score++;

    return Math.min(score, 4);
  }

  var STRENGTH_LABEL = [
    'Too short to be safe',
    'Weak — add a few more characters',
    'Getting there',
    'Strong',
    'Very strong'
  ];

  function bindStrengthMeter(input) {
    var field = input.closest('.field');
    var meter = $('[data-meter]', field);
    if (!meter) return;

    var fill = $('[data-meter-fill]', meter);
    var label = $('[data-meter-label]', meter);

    input.addEventListener('input', function () {
      if (!input.value) {
        meter.hidden = true;
        return;
      }

      var level = passwordStrength(input.value);

      meter.hidden = false;
      meter.dataset.level = String(level);
      fill.style.width = (level / 4) * 100 + '%';
      label.textContent = STRENGTH_LABEL[level];
    });
  }


  /* ----------------------------------------------------------
     Account and session
     ---------------------------------------------------------- */

  function getAccounts() {
    return store.read(KEYS.accounts, {});
  }

  function saveAccount(account) {
    var accounts = getAccounts();
    accounts[account.email] = account;
    return store.write(KEYS.accounts, accounts);
  }

  function findAccount(email) {
    return getAccounts()[email] || null;
  }

  /* The signed-in account, looked up fresh from the table each
     time rather than cached, so a password reset elsewhere in
     the same tab is always reflected immediately. */
  function getAccount() {
    var session = store.read(KEYS.session, null);
    return session ? findAccount(session.email) : null;
  }

  function isSignedIn() {
    return Boolean(getAccount());
  }

  function startSession(account) {
    store.write(KEYS.session, {
      email: account.email,
      since: Date.now()
    });
  }

  function endSession() {
    store.drop(KEYS.session);
  }

  function greetingForHour() {
    var hour = new Date().getHours();

    if (hour < 5) return 'Still awake';
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  }

  function paintAccount() {
    var account = getAccount();
    if (!account) return;

    var firstName = account.name.split(' ')[0];

    $('#greeting').textContent = greetingForHour() + ',';
    $('#display-name').textContent = firstName;
    $('#profile-name').textContent = account.name;
    $('#profile-email').textContent = account.email;
    $('#profile-since').textContent = 'With MITHRA since ' + calendarDate(account.createdAt);
  }


  /* ----------------------------------------------------------
     Routing
     ---------------------------------------------------------- */

  var appShell = $('#app');
  var currentView = 'splash';

  function showView(name) {
    /* Signed-out users never reach the app views by guessing. */
    if (APP_VIEWS.indexOf(name) > -1 && !isSignedIn()) {
      name = 'login';
    }

    var target = $('#view-' + name);
    if (!target) return;

    $all('.view').forEach(function (view) { view.hidden = true; });

    appShell.hidden = APP_VIEWS.indexOf(name) === -1;
    target.hidden = false;
    currentView = name;

    var activeTab = TAB_FOR[name] || name;

    $all('.tab').forEach(function (tab) {
      if (tab.dataset.goto === activeTab) {
        tab.setAttribute('aria-current', 'page');
      } else {
        tab.removeAttribute('aria-current');
      }
    });

    if (name === 'home' || name === 'profile') paintAccount();
    if (name === 'language') paintLanguagePicker();
    if (name === 'diary') renderEntries();

    if (name === 'chat') {
      paintLanguagePill();
      openThread();
    }

    window.scrollTo(0, 0);
  }

  /* One delegated listener covers every navigation control. */
  document.addEventListener('click', function (event) {
    var jump = event.target.closest('[data-goto]');
    if (jump) {
      showView(jump.dataset.goto);
      return;
    }

    var note = event.target.closest('[data-toast]');
    if (note) {
      toast(note.dataset.toast);
      return;
    }

    if (event.target.closest('[data-ask]')) {
      askMithra(null);
      return;
    }

    var seed = event.target.closest('[data-prompt]');
    if (seed) askMithra(seed.dataset.prompt);
  });

  /* Ask MITHRA never lands straight in the thread: the language
     has to be settled first, as in the wireframe. */
  var pendingPrompt = null;

  function askMithra(prompt) {
    pendingPrompt = prompt || null;
    showView(getLanguage() ? 'chat' : 'language');
  }


  /* ----------------------------------------------------------
     Password reveal
     ---------------------------------------------------------- */

  $all('[data-reveal]').forEach(function (button) {
    button.addEventListener('click', function () {
      var input = document.getElementById(button.dataset.reveal);
      var showing = input.type === 'text';

      input.type = showing ? 'password' : 'text';
      button.setAttribute('aria-pressed', String(!showing));
      button.setAttribute('aria-label', showing ? 'Show password' : 'Hide password');
      $('use', button).setAttribute('href', showing ? '#i-eye' : '#i-eye-off');

      input.focus();
    });
  });

  $all('.field--password input[autocomplete="new-password"]').forEach(bindStrengthMeter);


  /* ----------------------------------------------------------
     Sign up
     ---------------------------------------------------------- */

  $('#form-signup').addEventListener('submit', function (event) {
    event.preventDefault();

    var form = event.currentTarget;
    clearErrors(form);

    var name = $('#signup-name').value.trim();
    var email = $('#signup-email').value.trim().toLowerCase();
    var password = $('#signup-password').value;
    var valid = true;

    if (name.length < 2) {
      setError('signup-name', 'Tell MITHRA what to call you.');
      valid = false;
    }

    if (!EMAIL_PATTERN.test(email)) {
      setError('signup-email', 'That email address looks incomplete.');
      valid = false;
    }

    if (password.length < MIN_PASSWORD) {
      setError('signup-password', 'Use at least ' + MIN_PASSWORD + ' characters.');
      valid = false;
    }

    if (!valid) {
      focusFirstError(form);
      return;
    }

    if (findAccount(email)) {
      setError('signup-email', 'An account with this email already exists.');
      focusFirstError(form);
      return;
    }

    var salt = randomSalt();

    hashPassword(password, salt)
      .then(function (digest) {
        var saved = saveAccount({
          name: name,
          email: email,
          salt: salt,
          digest: digest,
          createdAt: Date.now()
        });

        if (!saved) {
          toast('This browser is blocking storage, so the account could not be saved.', 'error');
          return;
        }

        form.reset();
        $('[data-meter]', form).hidden = true;

        toast('Account created. Log in to continue.', 'success');
        setTimeout(function () { showView('login'); }, 900);
      })
      .catch(function () {
        toast('Something went wrong creating the account. Please try again.', 'error');
      });
  });


  /* ----------------------------------------------------------
     Log in
     ---------------------------------------------------------- */

  $('#form-login').addEventListener('submit', function (event) {
    event.preventDefault();

    var form = event.currentTarget;
    clearErrors(form);

    var email = $('#login-email').value.trim().toLowerCase();
    var password = $('#login-password').value;

    if (!EMAIL_PATTERN.test(email)) {
      setError('login-email', 'That email address looks incomplete.');
      focusFirstError(form);
      return;
    }

    var account = findAccount(email);

    if (!account) {
      setError('login-email', 'No account uses this email on this device.');
      focusFirstError(form);
      return;
    }

    hashPassword(password, account.salt)
      .then(function (digest) {
        if (digest !== account.digest) {
          setError('login-password', "That password doesn't match.");
          focusFirstError(form);
          return;
        }

        startSession(account);

        /* Confirm the session actually landed before treating
           this as a successful login — if storage is silently
           refusing writes, isSignedIn() will say so here rather
           than the app looking like it's just stuck on login. */
        if (!isSignedIn()) {
          toast('This browser is blocking storage, so login could not be saved.', 'error');
          return;
        }

        form.reset();
        paintAccount();

        toast('Welcome back, ' + account.name.split(' ')[0] + '.', 'success');
        showView('home');
      })
      .catch(function () {
        toast('Something went wrong logging in. Please try again.', 'error');
      });
  });


  var pendingReset = null;

  /* ----------------------------------------------------------
     Forgot password
     ---------------------------------------------------------- */

  $('#form-forgot').addEventListener('submit', function (event) {
    event.preventDefault();

    var form = event.currentTarget;
    clearErrors(form);

    var email = $('#forgot-email').value.trim().toLowerCase();

    if (!EMAIL_PATTERN.test(email)) {
      setError('forgot-email', 'That email address looks incomplete.');
      focusFirstError(form);
      return;
    }

    var account = findAccount(email);

    if (!account) {
      setError('forgot-email', 'No account on this device uses that address.');
      focusFirstError(form);
      return;
    }

    pendingReset = email;
    form.reset();
    showView('reset');
  });


  /* ----------------------------------------------------------
     Set a new password
     ---------------------------------------------------------- */

  $('#form-reset').addEventListener('submit', function (event) {
    event.preventDefault();

    var form = event.currentTarget;
    clearErrors(form);

    var password = $('#reset-password').value;
    var confirm = $('#reset-confirm').value;
    var account = pendingReset ? findAccount(pendingReset) : null;
    var valid = true;

    if (password.length < MIN_PASSWORD) {
      setError('reset-password', 'Use at least ' + MIN_PASSWORD + ' characters.');
      valid = false;
    }

    if (password !== confirm) {
      setError('reset-confirm', 'The two passwords are different.');
      valid = false;
    }

    if (!valid) {
      focusFirstError(form);
      return;
    }

    if (!account) {
      toast("That reset link expired. Let's start again.", 'error');
      showView('forgot');
      return;
    }

    var salt = randomSalt();

    hashPassword(password, salt)
      .then(function (digest) {
        account.salt = salt;
        account.digest = digest;
        saveAccount(account);

        pendingReset = null;
        form.reset();
        $('[data-meter]', form).hidden = true;

        toast('Password saved. Log in with your new password.', 'success');
        setTimeout(function () { showView('login'); }, 900);
      })
      .catch(function () {
        toast('Something went wrong saving the password. Please try again.', 'error');
      });
  });


  /* ----------------------------------------------------------
     Log out
     ---------------------------------------------------------- */

  $('#logout').addEventListener('click', function () {
    endSession();
    toast('Logged out.', 'success');
    setTimeout(function () { showView('welcome'); }, 500);
  });


  /* ============================================================
     CONVERSATION
     ============================================================ */

  var thread = $('#thread');
  var chatForm = $('#form-chat');
  var chatInput = $('#chat-input');
  var sendButton = $('.composer__send', chatForm);

  var history = [];
  var replying = false;

  function loadHistory() {
    var saved = store.read(KEYS.thread, null);
    return Array.isArray(saved) ? saved : [];
  }

  function saveHistory() {
    /* Keep the tail only. A runaway thread should not fill the
       storage quota and break the account alongside it. */
    if (history.length > 200) history = history.slice(-200);
    store.write(KEYS.thread, history);
  }

  function renderBubble(entry, animate) {
    var bubble = el('div', 'bubble bubble--' + entry.role);
    if (!animate) bubble.style.animation = 'none';

    bubble.appendChild(el('p', null, entry.text));
    bubble.appendChild(el('time', 'bubble__time', clockTime(entry.at)));

    thread.appendChild(bubble);
    return bubble;
  }

  function renderDivider(stamp) {
    thread.appendChild(el('p', 'thread__day', calendarDate(stamp)));
  }

  function scrollToLatest() {
    thread.scrollTop = thread.scrollHeight;
  }

  function openThread() {
    thread.innerHTML = '';

    if (!history.length) {
      var greeting = { role: 'ai', text: pack().opening, at: Date.now() };
      history.push(greeting);
      saveHistory();
    }

    var lastDay = '';

    history.forEach(function (entry) {
      var day = calendarDate(entry.at);

      if (day !== lastDay) {
        renderDivider(entry.at);
        lastDay = day;
      }

      if (entry.role === 'note') {
        var note = el('div', 'bubble bubble--note');
        note.style.animation = 'none';
        note.appendChild(el('p', null, entry.text));
        thread.appendChild(note);
      } else {
        renderBubble(entry, false);
      }
    });

    scrollToLatest();
    setTimeout(function () { chatInput.focus(); }, 60);
  }

  function push(role, text) {
    var entry = { role: role, text: text, at: Date.now() };

    history.push(entry);
    saveHistory();

    if (role === 'note') {
      var note = el('div', 'bubble bubble--note');
      note.appendChild(el('p', null, text));
      thread.appendChild(note);
    } else {
      renderBubble(entry, true);
    }

    scrollToLatest();
  }

  function showTyping() {
    var dots = el('div', 'typing');
    dots.id = 'typing';
    dots.setAttribute('aria-label', 'MITHRA is typing');

    for (var i = 0; i < 3; i++) dots.appendChild(el('span'));

    thread.appendChild(dots);
    scrollToLatest();
  }

  function hideTyping() {
    var dots = $('#typing');
    if (dots) dots.remove();
  }

  /* Reply length drives the pause, so short answers do not sit
     behind a fixed delay and long ones do not arrive instantly. */
  function typingDelay(reply) {
    return Math.min(1600, 450 + reply.length * 9);
  }

  function send(text) {
    var message = (text || chatInput.value).trim();
    if (!message || replying) return;

    push('me', message);

    chatInput.value = '';
    replying = true;
    sendButton.disabled = true;

    var reply = composeReply(message);
    var needsCare = isHeavy(message);

    showTyping();

    setTimeout(function () {
      hideTyping();
      push('ai', reply);

      if (needsCare) push('note', pack().care.replace('{help}', HELPLINE));

      replying = false;
      sendButton.disabled = false;
      chatInput.focus();
    }, typingDelay(reply));
  }

  chatForm.addEventListener('submit', function (event) {
    event.preventDefault();
    send();
  });

  $('#clear-thread').addEventListener('click', function () {
    history = [];
    store.drop(KEYS.thread);
    openThread();
    toast('Conversation cleared.');
  });

  $('#wipe-history').addEventListener('click', function () {
    history = [];
    store.drop(KEYS.thread);
    toast('Conversation history deleted.', 'success');
  });


  /* ----------------------------------------------------------
     Language

     The wireframe puts a language choice in front of the very
     first message, so every reply set below is written natively
     rather than translated from the English one. "Other" takes a
     free-text name and falls back to the English replies until a
     real model is wired in.
     ---------------------------------------------------------- */

  var LANGUAGE_NAMES = {
    ta: 'தமிழ்',
    en: 'English',
    tanglish: 'Tanglish',
    hinglish: 'Hinglish',
    other: 'Other'
  };

  function getLanguage() {
    var saved = store.read(KEYS.language, null);
    return saved && LANGUAGE_NAMES[saved.id] ? saved : null;
  }

  function languageLabel() {
    var lang = getLanguage();
    if (!lang) return LANGUAGE_NAMES.en;
    return lang.id === 'other' ? lang.custom : LANGUAGE_NAMES[lang.id];
  }

  function paintLanguagePill() {
    $('#chat-language-label').textContent = languageLabel();
  }

  var PACKS = {

    en: {
      opening: "Hi, I'm MITHRA. Tell me what's going on — I'll take it at your pace.",
      heavy: "I'm glad you told me. That's a lot to carry on your own, and you shouldn't have to.",
      care: 'MITHRA listens, but it is not a professional. Please talk to someone you trust, or call {help}.',
      rules: [
        [/\b(hi|hello|hey|namaste|vanakkam)\b/, 'Hello. How has your day been treating you?'],
        [/\b(sad|low|down|upset|crying|lonely|alone)\b/, "That sounds heavy. I'm here — what brought it on?"],
        [/\b(stress|stressed|pressure|overwhelm|tension|burnout)\b/, "Let's put it down piece by piece. Which part is pressing hardest?"],
        [/\b(anxious|anxiety|worried|nervous|panic|scared|afraid)\b/, 'Try one slow breath with me. What is the worry circling around?'],
        [/\b(exam|exams|study|studies|marks|result|college|semester)\b/, "Exams swallow everything else. What's the nearest deadline?"],
        [/\b(sleep|insomnia|tired|exhausted|awake)\b/, 'Rest gets hard when the mind stays busy. What keeps you up?'],
        [/\b(family|parents|home|amma|appa|mom|dad|brother|sister)\b/, 'Family things cut deeper than most. What happened?'],
        [/\b(angry|anger|furious|irritated|frustrated|annoyed)\b/, 'Anger usually guards something softer. What set it off?'],
        [/\b(happy|excited|glad|great|relieved|good news)\b/, "That's good to hear. What made it happen?"],
        [/\b(thank|thanks|nandri)\b/, "Any time. I'm right here whenever you want to talk."],
        [/\b(bye|goodbye|good night|see you)\b/, 'Take care of yourself. Come back whenever you need to.'],
        [/\b(who are you|what are you|your name)\b/, "I'm MITHRA — man ka mitra, a friend for your mind."]
      ],
      reflections: [
        "I hear you. What's behind that?",
        "Go on — I'm listening.",
        'That makes sense. How did it leave you feeling?',
        'Thanks for telling me. What happened next?',
        "Take your time. What else is sitting with you?"
      ]
    },

    ta: {
      opening: 'வணக்கம், நான் MITHRA. மனதில் இருப்பதை நிதானமாக சொல்லுங்கள், நான் கேட்கிறேன்.',
      heavy: 'சொன்னதற்கு நன்றி. இவ்வளவு பாரத்தை தனியாக சுமக்க வேண்டிய அவசியம் இல்லை.',
      care: 'MITHRA ஒரு நண்பன் மட்டுமே, மருத்துவர் அல்ல. நம்பிக்கையான ஒருவரிடம் பேசுங்கள், அல்லது {help} என்ற எண்ணை அழையுங்கள்.',
      rules: [
        [/வணக்கம்|ஹலோ|ஹாய்|hi|hello/, 'வணக்கம். இன்று மனநிலை எப்படி இருக்கிறது?'],
        [/சோக|வருத்த|கவலை|அழு|தனிமை/, 'அது கனமாக இருக்கும். என்ன நடந்தது என்று சொல்லுங்கள்.'],
        [/மன அழுத்த|டென்ஷன்|பதற்ற|பயம்/, 'ஒரு மூச்சு நிதானமாக விடுங்கள். எது அதிகமாக அழுத்துகிறது?'],
        [/தேர்வு|படிப்ப|மதிப்பெண்|கல்லூரி/, 'தேர்வு நேரம் எல்லாவற்றையும் விழுங்கிவிடும். அடுத்த தேர்வு எப்போது?'],
        [/தூக்க|உறக்க|சோர்வ/, 'மனம் ஓயாதபோது தூக்கம் வராது. என்ன யோசனை ஓடிக்கொண்டிருக்கிறது?'],
        [/அம்மா|அப்பா|வீட்|குடும்ப|அண்ண|தங்க/, 'வீட்டு விஷயங்கள் ஆழமாக பாதிக்கும். என்ன நடந்தது?'],
        [/கோப|எரிச்சல|வெறுப்ப/, 'கோபத்துக்குப் பின்னால் வேறு ஏதோ இருக்கும். எது தூண்டியது?'],
        [/சந்தோஷ|மகிழ்ச்சி|நல்ல செய்தி/, 'கேட்க சந்தோஷமாக இருக்கிறது. எப்படி நடந்தது?'],
        [/நன்றி|thanks/, 'எப்போது வேண்டுமானாலும் பேசுங்கள். நான் இங்கேதான் இருக்கிறேன்.'],
        [/பை|போய்ட்டு|குட் நைட்/, 'உங்களை பத்திரமாக பார்த்துக்கொள்ளுங்கள். எப்போது வேண்டுமானாலும் வாருங்கள்.']
      ],
      reflections: [
        'சொல்லுங்கள், நான் கேட்கிறேன்.',
        'புரிகிறது. அதற்கு பிறகு என்ன ஆனது?',
        'நீங்கள் சொல்வது சரிதான். இன்னும் கொஞ்சம் சொல்லுங்கள்.',
        'அவசரம் இல்லை. வேறு என்ன மனதில் இருக்கிறது?',
        'அது உங்களை எப்படி உணர வைத்தது?'
      ]
    },

    tanglish: {
      opening: 'Hey, naan MITHRA. Manasula irukradha nidhanama sollu, naan kekren.',
      heavy: 'Sonnadhukku nandri. Indha bharam ellam thaniya thooka vendam.',
      care: 'MITHRA oru friend dhan, doctor illa. Nambikkaiyana oruthar kitta pesu, illa {help} ku call pannu.',
      rules: [
        [/\b(vanakkam|hi|hello|hey|bro|da|machan)\b/, 'Hey! Nalla irukiya? Innaiku epdi poguthu?'],
        [/\b(sogam|kavala|kashtam|sad|azhu|thaniya)\b/, 'Adhu kashtam dhan. Enna nadandhuchu nu sollu.'],
        [/\b(tension|stress|paya|bayam|pressure)\b/, 'Konjam moochu vidu. Edhu adhigama tension kudukudhu?'],
        [/\b(exam|padi|padikka|mark|test|college)\b/, 'Exam neram ellame kadupu dhan. Next exam epo?'],
        [/\b(thookam|thoongala|sleep|sorvu|tired)\b/, 'Manasu ozhiyala na thookam varadhu. Enna yosichitu irukka?'],
        [/\b(amma|appa|veedu|family|anna|thangachi)\b/, 'Veettu vishayam konjam aazhama adikkum. Enna aachu?'],
        [/\b(kobam|erichal|kadupu|angry)\b/, 'Kobathukku pinnadi vera edho irukkum. Edhu trigger pannuchu?'],
        [/\b(santhosham|happy|nalla news|super)\b/, 'Kekka santhoshama iruku. Epdi nadandhuchu?'],
        [/\b(nandri|thanks|thank you)\b/, 'Eppo venumnalum pesu. Naan inga dhan iruken.'],
        [/\b(bye|poitu varen|good night|nite)\b/, 'Jaakradhaya iru. Eppo venumnalum vaa.']
      ],
      reflections: [
        'Sollu, naan kekren.',
        'Purinjudhu. Aprom enna aachu?',
        'Nee solradhu sari. Innum konjam sollu.',
        'Avasaram illa. Vera enna manasula iruku?',
        'Adhu unna epdi feel panna vechuchu?'
      ]
    },

    hinglish: {
      opening: 'Hey, main MITHRA hoon. Jo mann mein hai aaram se bata, main sun raha hoon.',
      heavy: 'Batane ke liye shukriya. Itna bojh akele uthana zaroori nahi hai.',
      care: 'MITHRA sirf ek dost hai, doctor nahi. Kisi bharose wale insaan se baat karo, ya {help} par call karo.',
      rules: [
        [/\b(namaste|hi|hello|hey|bhai|yaar|dost)\b/, 'Namaste! Aaj kaisa chal raha hai?'],
        [/\b(udaas|dukh|sad|rona|akela|akeli)\b/, 'Ye bhaari lag raha hai. Batao kya hua?'],
        [/\b(tension|stress|pareshan|dar|ghabra)\b/, 'Ek lambi saans lo. Sabse zyada kya chubh raha hai?'],
        [/\b(exam|padhai|marks|result|college)\b/, 'Exam ke dinon mein sab bhaari lagta hai. Agla paper kab hai?'],
        [/\b(neend|sona|thak|thaka)\b/, 'Dimaag chalta rahe to neend nahi aati. Kya soch rahe ho?'],
        [/\b(ghar|maa|papa|family|bhai|behen)\b/, 'Ghar ki baatein sabse gehri lagti hain. Kya hua?'],
        [/\b(gussa|chidh|naraz|khij)\b/, 'Gusse ke peeche aksar kuch aur hota hai. Kya hua tha?'],
        [/\b(khush|acchi khabar|mazaa|badhiya)\b/, 'Sunkar accha laga. Kaise hua ye?'],
        [/\b(shukriya|thanks|dhanyavaad)\b/, 'Kabhi bhi baat karo. Main yahin hoon.'],
        [/\b(bye|alvida|good night|chalta hoon)\b/, 'Apna khayal rakhna. Jab mann kare aa jaana.']
      ],
      reflections: [
        'Main sun raha hoon. Aur batao.',
        'Samajh raha hoon. Phir kya hua?',
        'Theek keh rahe ho. Thoda aur batao.',
        'Koi jaldi nahi. Aur kya chal raha hai mann mein?',
        'Usse tumhe kaisa mehsoos hua?'
      ]
    }
  };

  function pack() {
    var lang = getLanguage();
    if (!lang) return PACKS.en;
    return PACKS[lang.id] || PACKS.en;
  }


  /* ---------- Picker ---------- */

  var draftLanguage = null;
  var otherField = $('#language-other');
  var otherInput = $('#language-other-input');

  function paintLanguagePicker() {
    var saved = getLanguage();
    draftLanguage = saved ? saved.id : null;

    $all('.lang').forEach(function (option) {
      option.setAttribute('aria-checked', String(option.dataset.lang === draftLanguage));
    });

    otherField.hidden = draftLanguage !== 'other';
    otherInput.value = saved && saved.id === 'other' ? saved.custom : '';
    setError('language-other-input', '');
  }

  $all('.lang').forEach(function (option) {
    option.addEventListener('click', function () {
      draftLanguage = option.dataset.lang;

      $all('.lang').forEach(function (other) {
        other.setAttribute('aria-checked', String(other === option));
      });

      otherField.hidden = draftLanguage !== 'other';
      if (draftLanguage === 'other') otherInput.focus();
    });
  });

  $('#language-confirm').addEventListener('click', function () {
    if (!draftLanguage) {
      toast('Pick a language to continue.', 'error');
      return;
    }

    var custom = otherInput.value.trim();

    if (draftLanguage === 'other' && custom.length < 2) {
      setError('language-other-input', 'Type the language you want to use.');
      otherInput.focus();
      return;
    }

    var previous = languageLabel();
    var hadLanguage = Boolean(getLanguage());

    store.write(KEYS.language, { id: draftLanguage, custom: custom });
    paintLanguagePill();
    showView('chat');

    var now = languageLabel();

    var changed = !hadLanguage || now !== previous;

    if (changed && draftLanguage === 'other') {
      push('note', 'MITHRA cannot speak ' + custom + ' in this demo yet, so it will reply in English.');
    } else if (changed && hadLanguage) {
      push('note', 'Language switched to ' + now + '.');
    }

    if (pendingPrompt) {
      var seed = pendingPrompt;
      pendingPrompt = null;
      setTimeout(function () { send(seed); }, 160);
    }
  });


  /* ----------------------------------------------------------
     Demo replies

     A scripted stand-in for a real model. Rules match on intent
     within the chosen language, and the reflections catch
     everything else without repeating the same line twice.
     ---------------------------------------------------------- */

  var HEAVY_WORDS = [
    'hopeless', 'worthless', 'give up', 'end it', 'no point living',
    "can't go on", 'hurt myself', 'mudiyala', 'vazhkai vendam',
    'jeena nahi', 'sab khatam', 'வாழ முடியல', 'வேண்டாம் இந்த வாழ்க்கை'
  ];

  function isHeavy(message) {
    var text = message.toLowerCase();

    return HEAVY_WORDS.some(function (word) {
      return text.indexOf(word) > -1;
    });
  }

  var lastReflection = -1;

  function nextReflection(lines) {
    var index;

    do {
      index = Math.floor(Math.random() * lines.length);
    } while (index === lastReflection && lines.length > 1);

    lastReflection = index;
    return lines[index];
  }

  function composeReply(message) {
    var voice = pack();
    var text = message.toLowerCase();

    if (isHeavy(text)) return voice.heavy;

    for (var i = 0; i < voice.rules.length; i++) {
      if (voice.rules[i][0].test(text)) return voice.rules[i][1];
    }

    return nextReflection(voice.reflections);
  }


  /* ============================================================
     DIARY
     ============================================================ */

  var diaryForm = $('#form-diary');
  var diaryText = $('#diary-text');
  var diaryCount = $('#diary-count');
  var entriesBox = $('#entries');

  var MOOD_LABEL = {
    good: 'Good day',
    okay: 'Okay',
    low: 'Low',
    anxious: 'Anxious',
    angry: 'Angry'
  };

  var draftMood = null;

  function loadEntries() {
    var saved = store.read(KEYS.diary, null);
    return Array.isArray(saved) ? saved : [];
  }

  function saveEntries(list) {
    store.write(KEYS.diary, list);
  }

  function renderEntries() {
    var list = loadEntries();

    entriesBox.innerHTML = '';

    if (!list.length) {
      var empty = el('div', 'empty');
      empty.appendChild(el('strong', null, 'Nothing written yet'));
      empty.appendChild(el('p', null, 'The first line is the hardest. Anything counts.'));
      entriesBox.appendChild(empty);
      return;
    }

    list
      .slice()
      .sort(function (a, b) { return b.at - a.at; })
      .forEach(function (entry) {
        var card = el('article', 'entry');
        card.dataset.mood = entry.mood || '';

        var head = el('div', 'entry__head');
        head.appendChild(el('time', 'entry__date', calendarDate(entry.at) + ' · ' + clockTime(entry.at)));

        if (entry.mood) head.appendChild(el('span', 'entry__mood', MOOD_LABEL[entry.mood]));

        var drop = el('button', 'entry__drop');
        drop.type = 'button';
        drop.setAttribute('aria-label', 'Delete this entry');
        drop.innerHTML = '<svg class="icon"><use href="#i-trash"></use></svg>';
        drop.addEventListener('click', function () { removeEntry(entry.id); });

        card.appendChild(head);
        card.appendChild(el('p', 'entry__text', entry.text));
        card.appendChild(drop);

        entriesBox.appendChild(card);
      });
  }

  function removeEntry(id) {
    var kept = loadEntries().filter(function (entry) { return entry.id !== id; });

    saveEntries(kept);
    renderEntries();
    toast('Entry deleted.');
  }

  $all('[data-mood]').forEach(function (chip) {
    chip.addEventListener('click', function () {
      /* Tapping the selected mood again clears it. */
      draftMood = draftMood === chip.dataset.mood ? null : chip.dataset.mood;

      $all('[data-mood]').forEach(function (other) {
        other.setAttribute('aria-checked', String(other.dataset.mood === draftMood));
      });
    });
  });

  diaryText.addEventListener('input', function () {
    diaryCount.textContent = diaryText.value.length + ' / 2000';
  });

  diaryForm.addEventListener('submit', function (event) {
    event.preventDefault();

    var text = diaryText.value.trim();

    if (!text) {
      toast('Write something first.', 'error');
      diaryText.focus();
      return;
    }

    var list = loadEntries();

    list.push({
      id: 'e' + Date.now(),
      at: Date.now(),
      mood: draftMood,
      text: text
    });

    saveEntries(list);

    diaryText.value = '';
    diaryCount.textContent = '0 / 2000';
    draftMood = null;
    $all('[data-mood]').forEach(function (chip) { chip.setAttribute('aria-checked', 'false'); });

    renderEntries();
    toast('Entry saved.', 'success');
  });


  /* ============================================================
     BOOT
     ============================================================ */

  function boot() {
    history = loadHistory();

    setTimeout(function () {
      showView(isSignedIn() ? 'home' : 'welcome');
    }, SPLASH_MS);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
}());
