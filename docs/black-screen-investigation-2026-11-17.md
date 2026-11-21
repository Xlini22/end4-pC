# Nuova evidenza dei blocchi — 17 novembre 2026

## Aggiornamento riferito dall'utente il 20 novembre

Memtest86+ ha completato nove passaggi senza errori. Dopo uno scuotimento
violento del portatile, un presunto blocco e uno spegnimento forzato, l'utente
ha riavviato subito Memtest e riferito oltre 300 errori. Non sono disponibili
in questa nota indirizzi, test o bit degli errori: il dato non identifica
da solo banco RAM, slot, controller o scheda madre. Non ripetere movimenti
violenti per provocare il difetto.

La riproduzione riferita avviene fuori da Linux e dai plugin grafici, quindi
va distinta dai difetti visivi dei popup HyprGlass. I nove passaggi puliti non
escludono un problema intermittente. L'utente precisa che i blocchi nel boot
si presentano dopo altri blocchi durante l'uso, anziché come episodi isolati.
Restano prioritari backup dei dati e controllo fisico qualificato del percorso
della memoria. Le osservazioni di journal sotto sono quelle del 17 novembre.

Controlli esclusivamente su journal, /proc/cmdline e file del loader; nessun
rendering, interrogazione GPU, cambio sessione o modifica di parametri.

## Fatti osservati

- Kernel corrente 6.18.36-1-lts, boot `28e06b504019422292c74fd1bae48270`
  iniziato alle 10:26:34 CET. Binario ordinario HyprGlass assente; ticket
  monouso assente al controllo. Questo non certifica lo stato a ogni evento passato.
- Avvio non LTS confermato: `3256c0a35f4f4ad78e7f6221c480ce56`, 01:56:47,
  kernel 7.0.13-arch1-1. L'utente riferisce un blocco anche lì, senza nero;
  il log del kernel esaminato non conserva un errore corrispondente.
- Nel boot `9f9518df48ba435b89d1817c3c37c90a`, kernel LTS, alle 02:02:16:
  primo Oops (`[#1]`), general protection fault per indirizzo non canonico,
  `RIP: vma_interval_tree_remove+0x16f/0x300`, processo corrente hyprctl PID 5530.
  Call trace: vma_prepare → commit_merge → vma_expand → vma_merge_new_range
  → __mmap_region → do_mmap. Nessun frame AMDGPU nella call trace riportata.
- Il journal di quel boot prosegue fino alle 02:16:01: l'Oops non coincide
  necessariamente con un blocco totale immediato. Non chiamarlo kernel panic.
- L'utente riferisce episodi sia da fermo sia muovendo/scuotendo il portatile.
  Non provocare nuovi episodi con movimento o carico per verificarlo.

## Interpretazione e seguito

È un errore del kernel in gestione memoria, non un semplice crash applicativo.
La presenza di hyprctl identifica il contesto della chiamata, non la causa
originaria: non dimostra un difetto di hyprctl o del plugin. La traccia mostra
un accesso invalido; non distingue bug kernel/driver da instabilità hardware,
RAM, CPU, alimentazione o altro danneggiamento precedente delle strutture.
Non identifica la GPU come componente guasto e non dimostra saturazione RAM.

La [documentazione kernel](https://docs.kernel.org/admin-guide/reporting-issues.html)
spiega che dopo un primo Oops possono seguire problemi apparentemente
scollegati e che RAM difettosa può imitare bug del kernel. Non estendere questa
osservazione ai successivi boot come prova di uno stato software persistente.
La ricerca mirata non ha identificato una correzione verificata per questa
specifica traccia/versione. Il risultato non è una ricerca esaustiva dei bug.

Priorità: salvare i dati, mantenere il plugin disattivato, verifica memoria
fuori dal sistema installato e ispezione fisica qualificata visto il movimento
associato ad alcuni episodi. Un eventuale test memoria va predisposto e
concordato separatamente; non è stato installato o avviato. Un test negativo
non certifica assenza di guasti intermittenti. Nessuna reinstallazione,
aggiornamento BIOS o cambio casuale di driver prescritto come soluzione.

## Approfondimento statico e nuova interruzione

Confrontato il vmlinux installato, senza eseguirlo:
`/usr/lib/modules/6.18.36-1-lts/build/vmlinux`. Build ID
`7f5962ecfa4a9c75fb511222020686999720677b`, identico a quello dell'Oops.
L'offset `vma_interval_tree_remove+0x16f` contiene effettivamente
`mov 0x10(%rax),%rcx`. RAX nel dump è `0xffef8e1ec9d42808`; aggiungendo
0x10 si ottiene esattamente l'indirizzo invalido segnalato dal kernel.
Le istruzioni precedenti leggono un collegamento della struttura e ne
mascherano i bit bassi; l'operazione fallisce durante l'aggiornamento
dell'albero delle regioni virtuali associate a file, nel percorso mmap.
Non è un accesso GPU identificato dalla call trace.

Il valore ipotetico `0xffff8e1ec9d42818`, compatibile con gli indirizzi kernel
vicini nel dump, differisce dall'indirizzo errato per il solo bit 52:
XOR `0x0010000000000000`. Questo è un indizio compatibile con un bit alterato,
non prova che quello fosse il puntatore originale, né che l'alterazione
provenga da una cella RAM. Scritture errate, bug kernel/driver e instabilità
hardware restano da distinguere; nessun dump della memoria consente di
ricostruire la scrittura originaria. La ricerca svolta non ha individuato
una patch specifica verificata per questa firma.

L'utente riferisce un nuovo blocco mentre era lontano dal PC immobile,
seguito da tentativi di avvio con blocchi al boot/login e talvolta nessuna
immagine; dopo la sequenza il sistema torna utilizzabile per un periodo.
Riferisce inoltre un'associazione frequente tra indagini e blocchi. Gli ultimi
comandi locali comprendevano letture journal/proc e analisi readelf/objdump
del file kernel (circa 79 MB); nessun rendering, sysfs GPU, test di carico,
plugin load o cambio di parametri. Queste operazioni impiegano comunque
CPU, RAM e I/O: il loro ruolo come possibile innesco non è escluso dal fatto
che siano in sola lettura. Non ripeterle per provocare il problema.

Ultimo controllo limitato: nuovi boot LTS alle 12:10:30
(`3bd2ffd46928486e8c15bfad141642fe`), 12:13:36
(`cde61990dd1a4b76803010636360f099`) e 12:31:35
(`558ac497b896476996e4e1650a03f194`), nessun nuovo Oops/timeout GPU trovato
nei filtri del kernel conservato. Nel controllo corrente: binario ordinario
HyprGlass e ticket assenti. Non tutti i tentativi pre-journal risultano
necessariamente registrati. Nessuna misura identifica un componente pieno
o un persistente stato del driver tra riavvii. I successivi boot non sono
una continuazione del kernel che aveva subito l'Oops delle 02:02.

Analisi estese sospese dopo la segnalazione. Il passo diagnostico proposto
resta il controllo memoria fuori dall'OS installato e l'ispezione hardware,
preceduti dal salvataggio dei dati. Non predisposti né avviati automaticamente.

## Traccia conservata dal journal

```text
2026-11-17T02:02:16+01:00 archlinux kernel: Oops: general protection fault, probably for non-canonical address 0xffef8e1ec9d42818: 0000 [#1] SMP NOPTI
2026-11-17T02:02:16+01:00 archlinux kernel: CPU: 4 UID: 1000 PID: 5530 Comm: hyprctl Not tainted 6.18.36-1-lts #1 PREEMPT(voluntary)  7f5962ecfa4a9c75fb511222020686999720677b
2026-11-17T02:02:16+01:00 archlinux kernel: Hardware name: LENOVO 81UT/LNVNB161216, BIOS BUCN28WW 01/12/2021
2026-11-17T02:02:16+01:00 archlinux kernel: RIP: 0010:vma_interval_tree_remove+0x16f/0x300
2026-11-17T02:02:16+01:00 archlinux kernel: Code: 01 48 89 1f 31 ff 48 8b 48 10 48 89 10 48 8b 5c 24 18 48 8b 6c 24 20 eb 15 48 89 50 18 48 8b 00 48 83 f8 03 76 4a 48 83 e0 fc <48> 8b 48 10 48 8b 50 80 48 8b 70 c8 48 2b 90 78 ff ff ff 48 c1 ea
2026-11-17T02:02:16+01:00 archlinux kernel: RSP: 0018:ffffd0b9c31ab5b8 EFLAGS: 00010282
2026-11-17T02:02:16+01:00 archlinux kernel: RAX: ffef8e1ec9d42808 RBX: ffffd0b9c31ab748 RCX: 00000000000002cd
2026-11-17T02:02:16+01:00 archlinux kernel: RDX: 00000000000002cd RSI: 00000000000002cd RDI: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: RBP: ffffd0b9c31ab618 R08: ffff8e1ecc8d21e0 R09: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: R10: ffff8e1ed4371f00 R11: ffff8e1ed4371f88 R12: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: R13: 0000000000000000 R14: 00007fcd18cbd000 R15: ffff8e1dc1d11480
2026-11-17T02:02:16+01:00 archlinux kernel: FS:  0000000000000000(0000) GS:ffff8e1fc2eba000(0000) knlGS:0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
2026-11-17T02:02:16+01:00 archlinux kernel: CR2: 00007fcd18f5d298 CR3: 0000000109654000 CR4: 00000000003506f0
2026-11-17T02:02:16+01:00 archlinux kernel: Call Trace:
2026-11-17T02:02:16+01:00 archlinux kernel:  <TASK>
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? down_write+0x12/0x60
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  vma_prepare+0x12c/0x170
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  commit_merge+0xdc/0x290
2026-11-17T02:02:16+01:00 archlinux kernel:  vma_expand+0x97/0x1c0
2026-11-17T02:02:16+01:00 archlinux kernel:  vma_merge_new_range+0x7b/0x180
2026-11-17T02:02:16+01:00 archlinux kernel:  __mmap_region+0x4cf/0x1010
2026-11-17T02:02:16+01:00 archlinux kernel:  do_mmap+0x4bd/0x6c0
2026-11-17T02:02:16+01:00 archlinux kernel:  vm_mmap_pgoff+0x123/0x210
2026-11-17T02:02:16+01:00 archlinux kernel:  ksys_mmap_pgoff+0x15c/0x200
2026-11-17T02:02:16+01:00 archlinux kernel:  do_syscall_64+0x83/0x820
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? ksys_mmap_pgoff+0x168/0x200
2026-11-17T02:02:16+01:00 archlinux kernel:  ? prep_new_page+0xd3/0x1e0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? do_syscall_64+0x83/0x820
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? __alloc_frozen_pages_noprof+0x199/0x380
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? mod_memcg_lruvec_state+0xc5/0x1f0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? __lruvec_stat_mod_folio+0x85/0xd0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? __folio_mod_stat+0x2d/0x90
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? folio_add_new_anon_rmap+0x6b/0x1c0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? do_anonymous_page+0x674/0x9c0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? ___pte_offset_map+0x1b/0x160
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? __handle_mm_fault+0xa56/0xf00
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? count_memcg_events+0xc2/0x190
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? handle_mm_fault+0x1d7/0x2b0
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? do_user_addr_fault+0x237/0x710
2026-11-17T02:02:16+01:00 archlinux kernel:  ? srso_return_thunk+0x5/0x5f
2026-11-17T02:02:16+01:00 archlinux kernel:  ? exc_page_fault+0x8f/0x1d0
2026-11-17T02:02:16+01:00 archlinux kernel:  entry_SYSCALL_64_after_hwframe+0x76/0x7e
2026-11-17T02:02:16+01:00 archlinux kernel: RIP: 0033:0x7fcd18fb85ac
2026-11-17T02:02:16+01:00 archlinux kernel: Code: 1e fa 41 f7 c1 ff 0f 00 00 75 33 55 48 89 e5 41 54 41 89 cc 53 48 89 fb 48 85 ff 74 51 45 89 e2 48 89 df b8 09 00 00 00 0f 05 <48> 3d 00 f0 ff ff 77 24 5b 41 5c 5d c3 0f 1f 80 00 00 00 00 c7 05
2026-11-17T02:02:16+01:00 archlinux kernel: RSP: 002b:00007ffdb4e46090 EFLAGS: 00000206 ORIG_RAX: 0000000000000009
2026-11-17T02:02:16+01:00 archlinux kernel: RAX: ffffffffffffffda RBX: 00007fcd18c1d000 RCX: 00007fcd18fb85ac
2026-11-17T02:02:16+01:00 archlinux kernel: RDX: 0000000000000001 RSI: 00000000000a0000 RDI: 00007fcd18c1d000
2026-11-17T02:02:16+01:00 archlinux kernel: RBP: 00007ffdb4e460a0 R08: 0000000000000003 R09: 000000000021d000
2026-11-17T02:02:16+01:00 archlinux kernel: R10: 0000000000000812 R11: 0000000000000206 R12: 0000000000000812
2026-11-17T02:02:16+01:00 archlinux kernel: R13: 00007ffdb4e46120 R14: 00007ffdb4e46590 R15: 000000000021ce91
2026-11-17T02:02:16+01:00 archlinux kernel:  </TASK>
2026-11-17T02:02:16+01:00 archlinux kernel: Modules linked in: veth nf_conntrack_netlink xt_nat xt_tcpudp xt_conntrack xt_connmark xt_mark xt_cgroup xt_MASQUERADE bridge stp llc xfrm_user xfrm_algo xt_set ip_set nft_chain_nat nf_nat nf_conntrack nf_defrag_ipv6 nf_defrag_ipv4 xt_addrtype wireguard libcurve25519 ip6_udp_tunnel udp_tunnel xt_comment nft_compat nf_tables x_tables nfnetlink uinput ccm snd_seq_dummy rfcomm snd_hrtimer snd_seq snd_seq_device cmac algif_hash algif_skcipher overlay af_alg bnep intel_rapl_msr amd_atl intel_rapl_common snd_ctl_led snd_hda_codec_alc269 snd_hda_scodec_component ath10k_pci snd_hda_codec_realtek_lib snd_hda_codec_atihdmi joydev snd_hda_codec_generic snd_hda_codec_hdmi ath10k_core snd_hda_intel uvcvideo snd_hda_codec ath mousedev snd_hda_core kvm_amd videobuf2_vmalloc snd_intel_dspcfg uvc snd_intel_sdw_acpi mac80211 snd_hwdep videobuf2_memops videobuf2_v4l2 kvm ee1004 btusb snd_pcm videobuf2_common irqbypass sp5100_tco btmtk cfg80211 polyval_clmulni snd_timer btrtl ideapad_laptop videodev btbcm ghash_clmulni_intel
2026-11-17T02:02:16+01:00 archlinux kernel:  hid_rmi snd i2c_piix4 btintel aesni_intel platform_profile rmi_core bluetooth mc rapl pcspkr wmi_bmof sparse_keymap acpi_cpufreq libarc4 soundcore ccp k10temp i2c_smbus rfkill i2c_hid_acpi i2c_hid mac_hid i2c_dev crypto_user amdgpu dm_mod amdxcp i2c_algo_bit drm_ttm_helper ttm drm_exec drm_panel_backlight_quirks gpu_sched nvme drm_suballoc_helper drm_buddy nvme_core drm_display_helper nvme_keyring nvme_auth cec hkdf video wmi serio_raw
2026-11-17T02:02:16+01:00 archlinux kernel: ---[ end trace 0000000000000000 ]---
2026-11-17T02:02:16+01:00 archlinux kernel: RIP: 0010:vma_interval_tree_remove+0x16f/0x300
2026-11-17T02:02:16+01:00 archlinux kernel: Code: 01 48 89 1f 31 ff 48 8b 48 10 48 89 10 48 8b 5c 24 18 48 8b 6c 24 20 eb 15 48 89 50 18 48 8b 00 48 83 f8 03 76 4a 48 83 e0 fc <48> 8b 48 10 48 8b 50 80 48 8b 70 c8 48 2b 90 78 ff ff ff 48 c1 ea
2026-11-17T02:02:16+01:00 archlinux kernel: RSP: 0018:ffffd0b9c31ab5b8 EFLAGS: 00010282
2026-11-17T02:02:16+01:00 archlinux kernel: RAX: ffef8e1ec9d42808 RBX: ffffd0b9c31ab748 RCX: 00000000000002cd
2026-11-17T02:02:16+01:00 archlinux kernel: RDX: 00000000000002cd RSI: 00000000000002cd RDI: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: RBP: ffffd0b9c31ab618 R08: ffff8e1ecc8d21e0 R09: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: R10: ffff8e1ed4371f00 R11: ffff8e1ed4371f88 R12: 0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: R13: 0000000000000000 R14: 00007fcd18cbd000 R15: ffff8e1dc1d11480
2026-11-17T02:02:16+01:00 archlinux kernel: FS:  0000000000000000(0000) GS:ffff8e1fc2eba000(0000) knlGS:0000000000000000
2026-11-17T02:02:16+01:00 archlinux kernel: CS:  0010 DS: 0000 ES: 0000 CR0: 0000000080050033
2026-11-17T02:02:16+01:00 archlinux kernel: CR2: 00007fcd18f5d298 CR3: 0000000109654000 CR4: 00000000003506f0
```
