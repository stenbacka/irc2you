#!/usr/bin/perl -w
use strict;
use warnings;
use utf8;
use Encode;
use IO::Socket::UNIX;
use XML::LibXML;
use vars qw($VERSION %IRSSI);
use User::pwent;
use Data::Dumper;
use Irssi::TextUI;
use IO::Handle;
use POSIX;

use Log::Log4perl qw(:easy);
#Log::Log4perl->easy_init($INFO);

my $conf = q(
    log4perl.logger                    = DEBUG, FileApp
    log4perl.appender.FileApp          = Log::Log4perl::Appender::File
    log4perl.appender.FileApp.filename = irc2you-irssi-client.log
    log4perl.appender.FileApp.utf8     = 1
    log4perl.appender.FileApp.layout   = PatternLayout
    log4perl.appender.FileApp.layout.ConversionPattern = %p{1} %d> %m%n
);
Log::Log4perl->init( \$conf );

$VERSION = '0.01';
%IRSSI = (
    authors     => 'Tigge',
    contact     => 'tiggex@gmail.com',
    name        => 'sender',
    description => 'Sends stuff...',
    license     => 'None',
);

sub dbg {
    my ($string) = @_;
    Log::Log4perl::get_logger()->error(Encode::encode_utf8($string));
}

sub debug {
  my ($string) = @_;
  Log::Log4perl::get_logger()->debug($string);
}

sub info {
  my ($string) = @_;
  Log::Log4perl::get_logger()->info(Encode::encode_utf8($string));
}

sub warn {
  my ($string) = @_;
  Log::Log4perl::get_logger()->warning(Encode::encode_utf8($string));
}

my $socket = new IO::Socket::UNIX(Type => SOCK_STREAM, Peer => "/tmp/irc2you_socket") or die "Error $!\n";
my ($reader, $writer);
pipe($reader, $writer);
$writer->autoflush(1);

my $pid = fork();

if ($pid <= 0) {
    info("Starting receiver thread");
    close($reader);
    receivethread();
    info("Exiting receiver thread");
    close($writer);
    POSIX::_exit(1);
}

close($writer);
Irssi::pidwait_add($pid);
my $pipe_tag = Irssi::input_add(fileno($reader), Irssi::INPUT_READ, \&received, $reader);

my %context_buffer = ();
sub push_buffer {
  my ($server, $data, $nick, $address) = @_;
  my ($targ, $text) = split(/ :/, $data, 2);
  
  debug("Got privmsg event." );

  my $numRows = Irssi::settings_get_int('irc2you_context_rows');
  if(not defined $context_buffer{$targ}) {
    debug("First message for channel $targ");
    $context_buffer{$targ} = [];
  } else {
    debug("$targ buffer already defined");
    if((scalar @{$context_buffer{$targ}}) > $numRows) {
      shift(@{$context_buffer{$targ}});
    }
  }

  # Adds the newest element at the end of the array
  # Array size is one more than 'irc2you_context_rows' to keep count correct
  # after removing the hilight from the context
  @{$context_buffer{$targ}}[$numRows]={msg=>$text,from=>$nick,username=>$address,timestamp=>time()};
  debug("Buffered value: $text");
}

sub create_attached {
  my ($doc) = @_;
  debug("Determining if attached");
  my $screens = `screen -list`;
  $screens = "" if not defined $screens; # prevents warning messages
  my $ppid = getppid();
  my $attached    = $doc->createElement('attached');            
  if ($screens =~ m/$ppid.*\(Attached\)/) {
    debug("attached");
    $attached->appendText("true");
  } elsif ($screens =~ m/$ppid.*\(Detached\)/) {
    $attached->appendText("false");
  } else {
    $attached->appendText("true");
    debug("Not running in screen. Setting attached to true");
  }
  debug("Done Determining if attached");
  return $attached;
}

sub create_context {
  my ($doc,$targ) = @_;
  debug("Creating message context");
  my $context = $doc->createElement('context');
  foreach(@{$context_buffer{$targ}}) {
    my $ci = $doc->createElement('context_item');
    next if not defined($_);
    debug("Creating message context item");
    $ci->appendText($_->{msg});
    $ci->setAttribute("from",$_->{from});
    $ci->setAttribute("timestamp",$_->{timestamp});
    $ci->setAttribute("username",$_->{username});
    $context->appendChild($ci);
  }
  debug("Done Creating message context");
  return $context;
}

my $working;

sub sender {
    my ($text_dest, $text, $stripped_text) = @_;

    if(!$working) {

        $working = 1;
        dbg($text_dest);
        my $win  = $text_dest->{window};
        my $serv = $text_dest->{server};
        my $targ = $text_dest->{target};

        if(!$targ) {
            $working = 0;
            return;
        }

        if($targ =~ m/#/) {
            info("hilight in channel");
        } else {
            info("hilight from person");
        }

        info("target: '" . $targ ."'");
        #info("text: " . $text . ", " . $stripped_text);

        if (($text_dest->{level} & (Irssi::MSGLEVEL_HILIGHT() | Irssi::MSGLEVEL_MSGS())) && ($text_dest->{level} & Irssi::MSGLEVEL_NOHILIGHT()) == 0) {
            #my $test = new IO::Socket::UNIX(Type => SOCK_STREAM, Peer => "/tmp/irc2you_socket") or die "Error $!\n";

            my $doc = XML::LibXML::Document->new('1.0', "utf-8");
            my $element = $doc->createElement("notification");
            #my $user    = $doc->createElement('user');
            #my $username = getpwuid($<)->name;
            #$user->appendText($username);
            #$element->appendChild($user);

            #debug($stripped_text);
            if ($stripped_text =~ m/^<\s*(.*)\s*>/) {
              my $sender = $doc->createElement('sender');
              $sender->appendText(Encode::encode_utf8($1));
              $element->appendChild($sender);
            }

            my $mess    = $doc->createElement('message');
            my $last_msg = @{$context_buffer{$targ}}[-1];
            $mess->appendText(Encode::encode_utf8($last_msg->{msg})); #$stripped_text
            $element->appendChild($mess);

            my $chan    = $doc->createElement('channel');
            $chan->appendText(Encode::encode_utf8($targ));
            $element->appendChild($chan);

            my $away    = $doc->createElement('away');             
            $away->appendText($serv->{usermode_away} == 1 ? "true" : "false");
            $element->appendChild($away);

            $element->appendChild(create_attached($doc));

            $element->appendChild(create_context($doc,$targ));

            my $text = $element->toString();
            debug("sending message: '$text'");
            print $socket $element->toString();
            debug("messsage sent");
            print $socket "\n";
            #$test->close();
        }
        $working = 0;
   }
}



sub received {
    my $reader = shift;
    my $text   = <$reader>;
    
    if (!defined($text)) {
        close($reader);
        Irssi::input_remove($pipe_tag);  
    } else {
        info("received something on reader pipe");
        info("got: '$text'");
        info("$pid");
        
        my $dom = XML::LibXML->load_xml(string => $text);
        my $rn  = $dom->getDocumentElement();
        my $chn = $rn->getElementsByTagName("channel")->[0]->to_literal;
        my $mes = $rn->getElementsByTagName("message")->[0]->to_literal;
                
        my $server = Irssi::active_server();
        Irssi::Server::command($server, "/msg $chn $mes");
        info("sent '/msg $chn $mes'");
        
    }
}

sub receivethread {
    info("receive thread started");

    while (!eof($socket)) {
        defined( my $line = <$socket> )
            or die "readline failed: $!";
        info("got line from socket '$line'");
        print($writer $line);
    }
    info("receivethread killed");
    return;
}


sub terminate {
    info("Irssi is being terminated");
    shutdown($socket, 2);
}


info("Started irc2you irssi client");

Irssi::settings_add_int('irc2you', 'irc2you_context_rows', 4);

Irssi::signal_add("print text", 'sender');
Irssi::signal_add("event privmsg", 'push_buffer');
Irssi::signal_add("gui exit", 'terminate');

