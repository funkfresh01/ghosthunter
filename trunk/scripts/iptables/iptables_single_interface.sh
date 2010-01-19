#!/bin/bash

function show_help() {
	echo -e "\nA continuació es mostra un resum de les facilitats d'aquest filtre iptables.\n";
	echo -e "- Directives per defecte a DROP.";
	echo -e "- Loggin de tots els paquets estranys a través de Syslog: kernel.crit, modificable a partir de LOG_LEVEL";
	echo -e "- Anàlisis de paquets, cercant paquets típics provinents de escànners, com Nmap.";
	echo -e "- Utilització de taules d'usuari per a minimitzar el temps d'accés a la regla correcta.";
	echo -e "- Utilització de les capacitats \"tot estat\" de iptables, per a seguir les connexions.";
	echo -e "- Intent de simplificació de les regles, mitjançant el mòdul multiport.";
	
	echo -e "\n\n\nDepèn dels següents mòduls del kernel:";
	echo -e "--------------------------------------";
	echo -e "ip_conntrack";
	echo -e "ip_conntrack_ftp";
	echo -e "ipt_state";
	echo -e "ipt_multiport\n\n";
	
	echo -e "Com afegir un nou servei:";
	echo -e "-------------------------";
	echo -e "Hi han disponibles les variables CLIENTS_TCP, CLIENTS_UDP i SERVIDORS_TCP";
	echo -e "per obrir ports, sense tenir en compte el servei FTP. Aquestes variables admeten una";
	echo -e "llista de ports, separats pel caràcter \",\" i mai poden estar buides. En cas de no necessitar"
	echo -e "una d'aquestes variables, s'ha de comentar la regla corresponent, per a que el filtre no falli";
	echo -e "al inicialitzar-se.";
	echo -e "\nPer a escollir entre utilitzar servidor/client FTP, únicament s'hauran de comentar/descomentar les regles ofertes."
	echo -e "\n\n";

	echo -e "Definició de l'adreça local i la intefície:";
	echo -e "-------------------------------------------";
	echo -e "A continuació s'ofereixen les variables utilitzades, mitjançant un exemple:\n";
	echo -e 'IP_EXTERNA="192.168.1.105"':
	echo -e 'RANG_EXTERNA="192.168.1.0/24"';
	echo -e 'BROADCAST="192.168.1.255"';
	echo -e 'EXTERNAL_INTERFACE="eth0"';
}

function exit_error() {
	echo "error carregant un dels mòduls del kernel. Final d'execució"
	exit 0;
}

function default_accept() {
	echo "Directives per defecte a acceptar"
	$IPTABLES -P INPUT ACCEPT
	$IPTABLES -P OUTPUT  ACCEPT
	$IPTABLES -P FORWARD ACCEPT
}             

function flush_rules() {
	#Eliminar recles existents
	echo "Flushing iptables rules"
	$IPTABLES -F INPUT
	$IPTABLES -F OUTPUT
	$IPTABLES -F FORWARD
	$IPTABLES -F bad_tcp_packets
	$IPTABLES -F paquets_tcp
	$IPTABLES -F paquets_udp
	$IPTABLES -X
}

function start_filter() {

	echo "carregant mduls"
	modprobe ip_conntrack || exit_error
	modprobe ip_conntrack_ftp || exit_error
	modprobe ipt_state || exit_error
	modprobe ipt_multiport || exit_error

	# Directives per defecte
	$IPTABLES -P INPUT DROP
	$IPTABLES -P OUTPUT  DROP
	$IPTABLES -P FORWARD DROP


	#spoofing
	for f in /proc/sys/net/ipv4/conf/*/rp_filter; do
		echo 1 > $f;
	done
	#redireccions icmp
	for f in /proc/sys/net/ipv4/conf/*/accept_redirects; do
		echo 0 > $f;
	done
	#paquets d'origen enrutat
	for f in /proc/sys/net/ipv4/conf/*/accept_source_route; do
		echo 0 > $f;
	done



	# INSPECCIO DE PAQUETS MALFORMATS
	echo "creant taula bad_tcp_packets"
	$IPTABLES -N bad_tcp_packets

	#$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags SYN,ACK SYN,ACK \
	#	-m state --state NEW -j DROP

	##SCANS TIPICS DE nmap
	#$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags SYN,ACK,FIN,RST,PSH ACK -m state --state NEW \
	#	-j LOG  --log-level $LOG_LEVEL --log-prefix "bad_tcp_packets ACK scan : "
	#$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags ALL NONE \
	#	-j LOG  --log-level $LOG_LEVEL --log-prefix "bad_tcp_packets NULL scan : "
	#$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags SYN,ACK,FIN,RST,URG,PSH FIN,URG,PSH -m state --state NEW \
	#	-j LOG  --log-level $LOG_LEVEL --log-prefix "bad_tcp_packets XMAS scan : "
	#$IPTABLES -A bad_tcp_packets -p tcp --tcp-flags SYN,ACK,FIN,RST,URG,PSH FIN -m state --state NEW \
	#	-j LOG  --log-level $LOG_LEVEL --log-prefix "bad_tcp_packets FIN scan : "

	#$IPTABLES -A bad_tcp_packets -p tcp ! --syn -m state --state NEW -j DROP
	#	
	#$IPTABLES -A bad_tcp_packets -m state --state INVALID -j LOG --log-level $LOG_LEVEL \
	#	--log-prefix "bad_tcp_packets INVALID:" 
	#	
	#$IPTABLES -A bad_tcp_packets -m state --state INVALID -j DROP




	echo "creant taula paquets TCP"
	$IPTABLES -N paquets_tcp 

	#Habilita clients TCP
	$IPTABLES -A paquets_tcp -o $EXTERNAL_INTERFACE -p tcp --sport $UNPRIVPORTS \
		-m multiport --dports $CLIENTS_TCP -d $ANYWHERE  -m state \
		--state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A paquets_tcp -i $EXTERNAL_INTERFACE -p tcp -s $ANYWHERE --dport $UNPRIVPORTS \
		-m multiport --sports $CLIENTS_TCP -m state \
		--state ESTABLISHED -j ACCEPT

	#clanserver4u.de.quakenet.org
	$IPTABLES -A paquets_tcp -o $EXTERNAL_INTERFACE -p tcp --sport $UNPRIVPORTS \
		-m multiport --dports 6667 -d 194.124.229.58  -m state \
		--state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A paquets_tcp -i $EXTERNAL_INTERFACE -p tcp -s 194.124.229.58  --dport $UNPRIVPORTS \
		-m multiport --sports 6667 -m state \
		--state ESTABLISHED -j ACCEPT


	#client ftp
	#peticions
	$IPTABLES -A paquets_tcp -o $EXTERNAL_INTERFACE -p tcp  \
		--sport $UNPRIVPORTS -d $ANYWHERE --dport 21 -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A paquets_tcp -i $EXTERNAL_INTERFACE -p tcp -s $ANYWHERE --sport 21 \
		--dport $UNPRIVPORTS -m state --state ESTABLISHED -j ACCEPT
	#modus passiu
	$IPTABLES -A paquets_tcp -o $EXTERNAL_INTERFACE -p tcp  --sport $UNPRIVPORTS \
				-d $ANYWHERE --dport $UNPRIVPORTS -m state --state ESTABLISHED,RELATED -j ACCEPT
	$IPTABLES -A paquets_tcp -i $EXTERNAL_INTERFACE -p tcp -s $ANYWHERE --sport $UNPRIVPORTS \
				 --dport $UNPRIVPORTS -m state --state ESTABLISHED,RELATED -j ACCEPT	

	$IPTABLES -A paquets_tcp -j LOG --log-level $LOG_LEVEL --log-prefix "$LOG_PREFIX: "
	$IPTABLES -A paquets_tcp -p tcp -j DROP




	echo "creant taula paquets UDP"
	$IPTABLES -N paquets_udp
	
	#Habilita clients UDP

	$IPTABLES -A paquets_udp -o $EXTERNAL_INTERFACE -p udp --sport 123 \
		-m multiport --dports 123 -d $ANYWHERE  -m state \
		--state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A paquets_udp -i $EXTERNAL_INTERFACE -p udp -s $ANYWHERE --dport 123 \
		-m multiport --sports 123 -m state \
		--state ESTABLISHED -j ACCEPT

	$IPTABLES -A paquets_udp -o $EXTERNAL_INTERFACE -p udp --sport $UNPRIVPORTS \
		-m multiport --dports $CLIENTS_UDP -d $ANYWHERE  -m state \
		--state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A paquets_udp -i $EXTERNAL_INTERFACE -p udp -s $ANYWHERE --dport $UNPRIVPORTS \
		-m multiport --sports $CLIENTS_UDP -m state \
		--state ESTABLISHED -j ACCEPT

	$IPTABLES -A paquets_udp -i $EXTERNAL_INTERFACE -p udp -s $ANYWHERE  -m multiport --dports "137,138,5353"  -j DROP

	$IPTABLES -A paquets_udp -j LOG --log-level $LOG_LEVEL --log-prefix "$LOG_PREFIX: "
	$IPTABLES -A paquets_udp -p udp -j DROP




	#
	# AQUI COMENCEN LES REGLES
	#




	echo "comprovant paquets malformats"
	$IPTABLES -A INPUT -p tcp -j bad_tcp_packets
	$IPTABLES -A OUTPUT -p tcp -j bad_tcp_packets


	echo "habilitant loopback";
	#tràfic loopback
	$IPTABLES -A INPUT -i $LOOPBACK_INTERFACE -j ACCEPT
	$IPTABLES -A OUTPUT -o $LOOPBACK_INTERFACE  -j ACCEPT

	
	##broadcast i windows, que piquen a la porta ;-)
	$IPTABLES -A INPUT  -s $BROADCAST -j DROP;
	$IPTABLES -A OUTPUT  -d $BROADCAST -j DROP;



	echo "proteccions contra spoofing"

	#spoofing de calaix
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $CLASS_A -j DROP
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -d $CLASS_A -j DROP
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $CLASS_B -j DROP
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -d $CLASS_B -j DROP
#	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $CLASS_C -j DROP
#	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -d $CLASS_C -j DROP
	$IPTABLES -A INPUT  -d $BROADCAST_DEST -j DROP;
	$IPTABLES -A INPUT  -s $BROADCAST_DEST -j DROP;
	$IPTABLES -A OUTPUT  -d $BROADCAST_DEST -j DROP;
	$IPTABLES -A OUTPUT  -d $BROADCAST_DEST -j DROP;
	$IPTABLES -A INPUT  -d $BROADCAST_SRC -j DROP;
	$IPTABLES -A INPUT  -s $BROADCAST_SRC -j DROP;
	$IPTABLES -A OUTPUT  -d $BROADCAST_SRC -j DROP;
	$IPTABLES -A OUTPUT  -d $BROADCAST_SRC -j DROP;
	

	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $LOOPBACK -j DROP
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -d $LOOPBACK -j DROP

	# paquets de difusió mal formats
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $BROADCAST_DEST -j DROP 
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -d $BROADCAST_SRC -j DROP

	#adreçes experimentals i multidifusió de classe D
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $CLASS_D_MULTICAST -j DROP
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -s $CLASS_D_MULTICAST -j DROP

	#adreces privades classe E
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -s $CLASS_E_RESERVED_NET -j DROP



	$IPTABLES -A INPUT -p tcp -j paquets_tcp
	$IPTABLES -A OUTPUT -p tcp -j paquets_tcp


	$IPTABLES -A INPUT -p udp -j paquets_udp
	$IPTABLES -A OUTPUT -p udp -j paquets_udp


	echo "habilitant icmp restringit"
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 3   \
		-m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 3  \
		-m state --state ESTABLISHED -j ACCEPT

	#icmp SourceQuench (4)
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 4   \
		-j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 4  \
		-j ACCEPT

	#icmp Parameter Problem (12)
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 12 \
		-d $ANYWHERE -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 12 -s $ANYWHERE \
		-m state --state ESTABLISHED -j ACCEPT
	
	#icmp Destination Unreachable (3)
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 3 \
		-d $ANYWHERE -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 3 -s $ANYWHERE \
		-m state --state ESTABLISHED -j ACCEPT

	#icmp Time Exceeded (11)
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 11 \
		-d $ANYWHERE -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 11 -s $ANYWHERE \
		-m state --state ESTABLISHED -j ACCEPT


	#icmp Echo Request i Echo Reply (8/0)
	#fer ping
	$IPTABLES -A OUTPUT -o $EXTERNAL_INTERFACE -p icmp --icmp-type 8 \
		-d $ANYWHERE -m state --state NEW,ESTABLISHED -j ACCEPT
	$IPTABLES -A INPUT -i $EXTERNAL_INTERFACE -p icmp --icmp-type 0 -s $ANYWHERE \
		-m state --state ESTABLISHED -j ACCEPT
	
	
	echo "log de marcians"
	$IPTABLES -A INPUT -p icmp -j LOG --log-level $LOG_LEVEL --log-prefix "$LOG_PREFIX: "
	$IPTABLES -A OUTPUT -p icmp -j LOG --log-level $LOG_LEVEL --log-prefix "$LOG_PREFIX: "
	$IPTABLES -A INPUT -p icmp -j DROP
	$IPTABLES -A OUTPUT -p icmp -j DROP

}



#interfaces
EXTERNAL_INTERFACE="wlan0"
LOOPBACK_INTERFACE="lo"

CLIENTS_TCP="22,25,43,53,80,113,443,587,993,995,554,1863,5223,10000,1755"
CLIENTS_UDP="53,123,8767,27951,27960"

#loggin
#LOG_LEVEL="notice"
LOG_LEVEL="crit"
LOG_PREFIX="loggin de marcians: "

#adreces
IP_EXTERNA="192.168.1.105"
RANG_EXTERNA="192.168.1.0/24"
ANYWHERE="0.0.0.0/0"
LOOPBACK="127.0.0.0/8"
BROADCAST="192.168.1.255"

#constants spoofing
CLASS_A="10.0.0.0/8" 
CLASS_B="172.16.0.0/12"
CLASS_C="192.168.0.0/16"
CLASS_D_MULTICAST="224.0.0.0/4"
CLASS_E_RESERVED_NET="240.0.0.0/5"
BROADCAST_SRC="0.0.0.0"
BROADCAST_DEST="255.255.255.255"

#ports
PRIVPORTS="0:1023"
UNPRIVPORTS="1024:65535"

#fitxers
IPTABLES="/sbin/iptables"




case "$1" in
  start|restart)
  echo -e "\n\n****************************\n*\n* Filtre IpTables by msk :-)\n*\n****************************\n"
  flush_rules
  start_filter
  ;;
  stop)
  flush_rules
  default_accept
  ;;
  --help)
  show_help
  ;;
esac
